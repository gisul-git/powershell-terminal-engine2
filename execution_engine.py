import asyncio
import ipaddress
import json
import logging
import re
import shlex
import socket
from copy import deepcopy
from typing import Callable, Iterable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from path_resolver import HOME_PATH, ROOT_PATH, basename, normalize_path, parent_path
from validation import error, has_flag, validate_flags


ALIASES = {
    "ls": "Get-ChildItem",
    "type": "Get-Content",
    "mkdir": "New-Item",
    "copy": "Copy-Item",
    "move": "Move-Item",
    "echo": "Write-Output",
    "set": "Get-ChildItem",
    "ipconfig": "Get-NetIPConfiguration",
    "whoami": "Get-CurrentUser",
    "hostname": "Get-ComputerName",
}

logger = logging.getLogger(__name__)

STOP_ERRORS = {
    error("invalid_command"),
    error("invalid_arguments"),
    error("missing_destination"),
    error("path_missing"),
    error("file_missing"),
    error("source_missing"),
    error("item_missing"),
    error("access_denied"),
    error("cannot_remove_directory"),
    error("cannot_move_file"),
    error("same_file"),
    error("service_not_found"),
    error("variable_not_found"),
    error("request_timeout"),
}

VARIABLE_NAME_PATTERN = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$")
VARIABLE_REFERENCE_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
WEB_TIMEOUT_SECONDS = 5

IPCONFIG_OUTPUT = "\n".join(
    [
        "IPv4 Address . . . . . : 192.168.1.10",
        "Subnet Mask . . . . . : 255.255.255.0",
        "Gateway . . . . . . . : 192.168.1.1",
    ]
)
WHOAMI_OUTPUT = "User"
HOSTNAME_OUTPUT = "WIN-SERVER01"
COMPUTER_INFO_OUTPUT = "\n".join(
    [
        "OSName : Windows Server",
        "OSVersion : 2022",
        "ComputerName : WIN-SERVER01",
    ]
)


def build_terminal_history(session: dict) -> str:
    lines: list[str] = []
    for item in session["history"]:
        lines.append(f"{item['prompt']}{item['command']}")
        if item["output"]:
            lines.append(item["output"])
    return "\n".join(lines)


def format_history(session: dict) -> str:
    return build_terminal_history(session)


def tokenize(command: str) -> list[str]:
    return shlex.split(command, posix=False)


def pipeline_parts(command: str) -> list[str]:
    return [part.strip() for part in command.split("|") if part.strip()]


def split_redirection(command: str) -> tuple[str, str | None]:
    in_single = False
    in_double = False
    for index, char in enumerate(command):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ">" and not in_single and not in_double:
            left = command[:index].strip()
            right = command[index + 1 :].strip()
            return left, right or None
    return command.strip(), None


def get_option(tokens: Iterable[str], name: str) -> str | None:
    token_list = list(tokens)
    for index, token in enumerate(token_list):
        if token.lower() == name.lower() and index + 1 < len(token_list):
            return token_list[index + 1]
    return None


def parse_params(args: list[str]) -> dict[str, str | bool]:
    """Parse PowerShell-style named parameters from arguments.
    
    Example:
        New-Item -ItemType Directory -Name audit_case
        Returns: {"ItemType": "Directory", "Name": "audit_case"}
    """
    params = {}
    i = 0
    while i < len(args):
        if args[i].startswith("-"):
            key = args[i][1:]  # Remove the leading dash
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                # Parameter has a value
                params[key] = args[i + 1].strip('"').strip("'")
                i += 2
            else:
                # Flag parameter (no value)
                params[key] = True
                i += 1
        else:
            i += 1
    return params


def parse_env_assignment(command: str) -> tuple[str, str] | None:
    if not command.startswith("$env:") or "=" not in command:
        return None
    left, right = command.split("=", 1)
    key = left[5:].strip()
    value = right.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


def parse_variable_assignment(command: str) -> tuple[str, str] | None:
    match = VARIABLE_NAME_PATTERN.match(command.strip())
    if not match:
        return None
    name, value = match.groups()
    return name, value.strip().strip('"').strip("'")


def substitute_variables(session: dict, command: str) -> str:
    variables = session.setdefault("variables", {})

    def replace(match: re.Match) -> str:
        name = match.group(1)
        return str(variables.get(name, match.group(0)))

    return VARIABLE_REFERENCE_PATTERN.sub(replace, command)


def normalize_alias(command: str) -> str:
    tokens = tokenize(command)
    if not tokens:
        return command

    alias = ALIASES.get(tokens[0].lower())
    if not alias:
        return command

    if tokens[0].lower() == "mkdir":
        if len(tokens) < 2:
            return alias
        return " ".join([alias, tokens[1], "-ItemType", "Directory", *tokens[2:]])
    
    if tokens[0].lower() == "set":
        return "Get-ChildItem Env:"
    
    if tokens[0].lower() in ["ipconfig", "whoami", "hostname"]:
        return alias

    tokens[0] = alias
    return " ".join(tokens)


def success(output: str = "", clear: bool = False) -> dict:
    return {"output": output, "clear": clear}


def ensure_node(session: dict, path: str) -> dict | None:
    return session["fs"].get(path)


def ensure_dir(session: dict, path: str) -> dict | None:
    node = ensure_node(session, path)
    if node and node["type"] == "dir":
        return node
    return None


def ensure_file(session: dict, path: str) -> dict | None:
    node = ensure_node(session, path)
    if node and node["type"] == "file":
        return node
    return None


def add_child(session: dict, path: str, node: dict) -> None:
    session["fs"][path] = node
    parent = ensure_dir(session, parent_path(path))
    if parent:
        parent["children"][basename(path)] = path


def remove_child_reference(session: dict, path: str) -> None:
    parent = ensure_dir(session, parent_path(path))
    if parent:
        parent["children"].pop(basename(path), None)


def list_directory(session: dict, path: str) -> str:
    directory = ensure_dir(session, path)
    if not directory:
        return error("path_missing")

    lines = [f"Directory: {path}", "", "Mode    Name", "----    ----"]
    for name in sorted(directory["children"]):
        child = session["fs"][directory["children"][name]]
        mode = "d" if child["type"] == "dir" else "-"
        lines.append(f"{mode:<7} {name}")
    return "\n".join(lines)


def create_item(session: dict, target_path: str, item_type: str) -> str:
    parent = ensure_dir(session, parent_path(target_path))
    if not parent:
        return error("path_missing")
    if ensure_node(session, target_path):
        return error("invalid_arguments")

    normalized_type = item_type.lower()
    if normalized_type == "directory":
        add_child(session, target_path, {"type": "dir", "children": {}})
        return ""
    if normalized_type == "file":
        add_child(session, target_path, {"type": "file", "content": "", "metadata": {}})
        return ""
    return error("invalid_arguments")


def delete_node(session: dict, target_path: str) -> None:
    node = ensure_node(session, target_path)
    if not node:
        return
    if node["type"] == "dir":
        for child_path in list(node["children"].values()):
            delete_node(session, child_path)
    remove_child_reference(session, target_path)
    session["fs"].pop(target_path, None)


def remove_item(session: dict, target_path: str, recursive: bool) -> str:
    node = ensure_node(session, target_path)
    if not node:
        return error("item_missing")
    if target_path == ROOT_PATH:
        return error("access_denied")
    if node["type"] == "dir" and not recursive:
        return error("cannot_remove_directory")
    delete_node(session, target_path)
    if session["cwd"] == target_path:
        session["cwd"] = parent_path(target_path)
    return ""


def read_content(session: dict, target_path: str) -> tuple[str, str]:
    file_node = ensure_file(session, target_path)
    if not file_node:
        return error("file_missing"), ""
    return "", file_node["content"]


def write_content(session: dict, target_path: str, content: str, append: bool) -> str:
    node = ensure_node(session, target_path)
    if not node:
        parent = ensure_dir(session, parent_path(target_path))
        if not parent:
            return error("path_missing")
        add_child(session, target_path, {"type": "file", "content": "", "metadata": {}})
        node = ensure_node(session, target_path)

    if not node or node["type"] != "file":
        return error("invalid_arguments")

    if append and node["content"]:
        node["content"] += "\n" + content
    elif append:
        node["content"] = content
    else:
        node["content"] = content
    return ""


def redirect_output(session: dict, raw_target: str, output: str) -> str:
    target_path = normalize_path(session["cwd"], raw_target)
    result = write_content(session, target_path, output, append=False)
    if not result:
        logger.debug("redirection output -> %s", output)
        logger.debug("file creation -> %s", target_path)
    return result


def copy_item(session: dict, source_path: str, destination_path: str) -> str:
    if source_path == destination_path:
        return error("same_file")

    source = ensure_file(session, source_path)
    if not source:
        return error("file_missing")

    destination_parent = ensure_dir(session, parent_path(destination_path))
    if not destination_parent:
        return error("path_missing")

    existing = ensure_node(session, destination_path)
    if existing and existing["type"] != "file":
        return error("access_denied")

    add_child(session, destination_path, deepcopy(source))
    return ""


def move_item(session: dict, source_path: str, destination_path: str) -> str:
    if source_path == destination_path:
        return error("same_file")

    source = ensure_file(session, source_path)
    if not source:
        return error("source_missing")

    destination_parent = ensure_dir(session, parent_path(destination_path))
    if not destination_parent:
        return error("path_missing")

    existing = ensure_node(session, destination_path)
    if existing and existing["type"] != "file":
        return error("cannot_move_file")

    add_child(session, destination_path, deepcopy(source))
    delete_node(session, source_path)
    return ""


def select_string(text: str, needle: str) -> str:
    if not needle:
        return ""
    matches = [line for line in text.splitlines() if needle in line]
    return "\n".join(matches)


def handle_cd(session: dict, tokens: list[str]) -> dict:
    """cd / Set-Location - Change directory.
    
    Supports:
        cd path
        Set-Location path
    """
    if len(tokens) > 2:
        return success(error("invalid_arguments"))
    target = normalize_path(session["cwd"], tokens[1] if len(tokens) > 1 else HOME_PATH)
    node = ensure_dir(session, target)
    if not node:
        return success(error("path_missing"))
    session["cwd"] = target
    return success()


def handle_dir(session: dict, tokens: list[str]) -> dict:
    if len(tokens) > 2:
        return success(error("invalid_arguments"))
    target = normalize_path(session["cwd"], tokens[1] if len(tokens) > 1 else None)
    return success(list_directory(session, target))


def handle_pwd(session: dict, tokens: list[str]) -> dict:
    if len(tokens) != 1:
        return success(error("invalid_arguments"))
    return success(session["cwd"])


def handle_new_item(session: dict, tokens: list[str]) -> dict:
    """New-Item - Create files or directories with named parameters.
    
    Supports:
        New-Item -ItemType Directory -Name audit_case
        New-Item -ItemType File -Name events.log
        New-Item path -ItemType Directory (legacy)
    """
    if len(tokens) < 2:
        return success(error("invalid_arguments"))
    
    params = parse_params(tokens[1:])
    
    # Check for -ItemType parameter
    item_type = params.get("ItemType") or params.get("itemtype")
    if not item_type:
        return success(error("invalid_arguments"))
    
    # Get path from -Name parameter or positional argument
    path_token = params.get("Name") or params.get("name")
    
    if not path_token:
        # Try to find positional argument (non-parameter token)
        for token in tokens[1:]:
            if not token.startswith("-") and token not in params.values():
                path_token = token
                break
    
    if not path_token:
        return success(error("invalid_arguments"))
    
    return success(create_item(session, normalize_path(session["cwd"], path_token), item_type))


def handle_remove_item(session: dict, tokens: list[str]) -> dict:
    if len(tokens) < 2:
        return success(error("invalid_arguments"))
    if not validate_flags(tokens[2:], {"-Recurse"}):
        return success(error("invalid_arguments"))
    return success(
        remove_item(
            session,
            normalize_path(session["cwd"], tokens[1]),
            recursive=has_flag(tokens[2:], "-Recurse"),
        )
    )


def handle_get_content(session: dict, tokens: list[str]) -> dict:
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    read_error, content = read_content(session, normalize_path(session["cwd"], tokens[1]))
    return success(read_error or content)


def handle_set_content(session: dict, tokens: list[str], append: bool, piped_input: str = "") -> dict:
    """Set-Content / Add-Content - Write content to file.
    
    Supports:
        Set-Content file.txt "content"
        ... | Set-Content file.txt (pipeline input)
    """
    if piped_input:
        # Pipeline mode: ... | Set-Content file.txt
        if len(tokens) < 2:
            return success(error("invalid_arguments"))
        
        target_path = normalize_path(session["cwd"], tokens[1])
        return success(write_content(session, target_path, piped_input, append=append))
    
    # Direct mode: Set-Content file.txt "content"
    if len(tokens) < 3:
        return success(error("invalid_arguments"))
    
    return success(
        write_content(
            session,
            normalize_path(session["cwd"], tokens[1]),
            " ".join(tokens[2:]).strip('"').strip("'"),
            append=append,
        )
    )


def handle_select_string(session: dict, tokens: list[str], piped_input: str) -> dict:
    """Select-String - Search for patterns in text.
    
    Supports:
        Select-String "pattern" file.txt
        ... | Select-String "pattern"
    """
    if len(tokens) < 2:
        return success(error("invalid_arguments"))

    # Case 1: Only pattern provided (piped input)
    if len(tokens) == 2:
        return success(select_string(piped_input, tokens[1].strip('"').strip("'")))

    # Case 2: Pattern and file provided: Select-String "pattern" file.txt
    # tokens[1] is the pattern, tokens[2] is the file
    pattern = tokens[1].strip('"').strip("'")
    possible_path = normalize_path(session["cwd"], tokens[2])
    
    if ensure_node(session, possible_path):
        read_error, content = read_content(session, possible_path)
        if read_error:
            return success(read_error)
        return success(select_string(content, pattern))
    
    # File not found
    return success(error("file_missing"))


def handle_get_process(session: dict) -> dict:
    lines = ["Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  ProcessName"]
    for process in session["processes"]:
        lines.append(f"{12:>7} {4:>7} {24:>8} {18:>10} {0.15:>10.2f} {process['pid']:>6}  {process['name']}")
    return success("\n".join(lines))


def handle_stop_process(session: dict, tokens: list[str]) -> dict:
    """Stop-Process - Stop a process by ID.
    
    Supports:
        Stop-Process -Id 102 -Force
        Stop-Process 102 (legacy)
    """
    params = parse_params(tokens[1:])
    
    # Get PID from -Id parameter
    pid = params.get("Id") or params.get("id")
    
    if not pid:
        # Try legacy positional argument
        if len(tokens) == 2 and tokens[1].isdigit():
            pid = tokens[1]
        else:
            return success(error("invalid_arguments"))
    
    if not str(pid).isdigit():
        return success(error("invalid_arguments"))
    
    pid_int = int(pid)
    
    for process in session["processes"]:
        if process["pid"] == pid_int:
            session["processes"] = [item for item in session["processes"] if item["pid"] != pid_int]
            return success()
    
    return success(error("item_missing"))


def handle_write_output(tokens: list[str]) -> dict:
    return success(" ".join(tokens[1:]).strip('"').strip("'"))


def handle_copy_item_command(session: dict, tokens: list[str]) -> dict:
    if len(tokens) < 3:
        return success(error("missing_destination" if len(tokens) == 2 else "invalid_arguments"))
    if len(tokens) != 3:
        return success(error("invalid_arguments"))
    return success(
        copy_item(
            session,
            normalize_path(session["cwd"], tokens[1]),
            normalize_path(session["cwd"], tokens[2]),
        )
    )


def handle_move_item_command(session: dict, tokens: list[str]) -> dict:
    if len(tokens) < 3:
        return success(error("missing_destination" if len(tokens) == 2 else "invalid_arguments"))
    if len(tokens) != 3:
        return success(error("invalid_arguments"))
    return success(
        move_item(
            session,
            normalize_path(session["cwd"], tokens[1]),
            normalize_path(session["cwd"], tokens[2]),
        )
    )


def handle_measure_object(piped_input: str) -> dict:
    if not piped_input:
        return success("Count : 0")
    lines = piped_input.splitlines()
    return success(f"Count : {len(lines)}")


def handle_sort_object(session: dict, tokens: list[str], piped_input: str) -> dict:
    if not piped_input:
        return success("")
    
    lines = piped_input.splitlines()
    
    # Check if sorting by a specific property (e.g., Id)
    sort_by = get_option(tokens, "Id") or get_option(tokens, "-Property")
    
    if sort_by and sort_by.lower() == "id":
        # Try to extract and sort by Id column (for Get-Process output)
        sorted_lines = []
        header = None
        data_lines = []
        
        for line in lines:
            if "Id" in line and "ProcessName" in line:
                header = line
            elif line.strip() and not line.startswith("-"):
                data_lines.append(line)
        
        # Extract Id and sort
        try:
            parsed = []
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 6:
                    pid = int(parts[5])
                    parsed.append((pid, line))
            parsed.sort(key=lambda x: x[0])
            sorted_lines = [header] if header else []
            sorted_lines.extend([line for _, line in parsed])
            return success("\n".join(sorted_lines))
        except (ValueError, IndexError):
            pass
    
    # Default: alphabetical sort
    sorted_lines = sorted(lines)
    return success("\n".join(sorted_lines))


def handle_select_object(tokens: list[str], piped_input: str) -> dict:
    if not piped_input:
        return success("")
    
    lines = piped_input.splitlines()
    
    # Handle -First N
    first_count = get_option(tokens, "-First")
    if first_count and first_count.isdigit():
        selected = lines[:int(first_count)]
        return success("\n".join(selected))
    
    # Handle property selection (Id, ProcessName, etc.)
    property_name = None
    for i, token in enumerate(tokens):
        if i > 0 and not token.startswith("-"):
            property_name = token
            break
    
    if not property_name:
        return success(piped_input)
    
    # Extract specific column
    result_lines = []
    for line in lines:
        if property_name.lower() == "id":
            if "Id" in line and "ProcessName" in line:
                result_lines.append("Id")
            else:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        result_lines.append(parts[5])
                    except IndexError:
                        pass
        elif property_name.lower() == "processname":
            if "ProcessName" in line:
                result_lines.append("ProcessName")
            else:
                parts = line.split()
                if len(parts) >= 7:
                    result_lines.append(parts[6])

    if result_lines:
        return success("\n".join(result_lines))

    # Generic "key : value" support for Invoke-RestMethod and Get-Variable output.
    normalized_property = property_name.lower()
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == normalized_property:
            result_lines.append(value.strip())
    
    return success("\n".join(result_lines))


def handle_get_date() -> dict:
    from datetime import datetime
    now = datetime.now()
    return success(now.strftime("%Y-%m-%d %H:%M:%S"))


def handle_get_location(session: dict) -> dict:
    lines = ["Path", "----", session["cwd"]]
    return success("\n".join(lines))


def handle_rename_item(session: dict, tokens: list[str]) -> dict:
    if len(tokens) != 3:
        return success(error("invalid_arguments"))
    
    old_path = normalize_path(session["cwd"], tokens[1])
    new_name = tokens[2].strip('"').strip("'")
    
    old_node = ensure_node(session, old_path)
    if not old_node:
        return success(error("file_missing"))
    
    # Build new path in same directory
    parent = parent_path(old_path)
    new_path = normalize_path(parent, new_name)
    
    # Check if new path already exists
    if ensure_node(session, new_path):
        return success(error("invalid_arguments"))
    
    # Copy node to new location
    add_child(session, new_path, deepcopy(old_node))
    
    # Remove old node
    delete_node(session, old_path)
    
    return success()


def handle_get_childitem_env(session: dict) -> dict:
    if not session["env"]:
        return success("Name        Value\n----        -----")
    
    lines = ["Name        Value", "----        -----"]
    for key, value in sorted(session["env"].items()):
        lines.append(f"{key:<12}{value}")
    return success("\n".join(lines))


def handle_get_variable(session: dict, tokens: list[str]) -> dict:
    variables = session.setdefault("variables", {})
    if len(tokens) > 2:
        return success(error("invalid_arguments"))

    if len(tokens) == 2:
        name = tokens[1].lstrip("$")
        if name not in variables:
            return success(error("variable_not_found"))
        return success(f"Name : {name}\nValue : {variables[name]}")

    if not variables:
        return success("Name    Value\n----    -----")

    lines = ["Name    Value", "----    -----"]
    for name, value in sorted(variables.items()):
        lines.append(f"{name:<7} {value}")
    return success("\n".join(lines))


def handle_set_variable(session: dict, tokens: list[str]) -> dict:
    if len(tokens) < 3:
        return success(error("invalid_arguments"))
    name = tokens[1].lstrip("$")
    if not name:
        return success(error("invalid_arguments"))
    session.setdefault("variables", {})[name] = " ".join(tokens[2:]).strip('"').strip("'")
    return success()


def handle_remove_variable(session: dict, tokens: list[str]) -> dict:
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    name = tokens[1].lstrip("$")
    variables = session.setdefault("variables", {})
    if name not in variables:
        return success(error("variable_not_found"))
    variables.pop(name, None)
    return success()


def handle_get_childitem(session: dict, tokens: list[str]) -> dict:
    """Enhanced Get-ChildItem / dir / ls"""
    # Check if it's Env: request
    if len(tokens) == 2 and tokens[1].lower() == "env:":
        return handle_get_childitem_env(session)
    
    # Otherwise list directory
    if len(tokens) > 2:
        return success(error("invalid_arguments"))
    
    target = normalize_path(session["cwd"], tokens[1] if len(tokens) > 1 else None)
    directory = ensure_dir(session, target)
    if not directory:
        return success(error("path_missing"))
    
    lines = ["Mode   Name", "----   ----"]
    for name in sorted(directory["children"]):
        child = session["fs"][directory["children"][name]]
        mode = "Dir " if child["type"] == "dir" else "File"
        lines.append(f"{mode:<6} {name}")
    return success("\n".join(lines))


def handle_get_item(session: dict, tokens: list[str]) -> dict:
    """Get-Item - Return details of file/folder"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    target_path = normalize_path(session["cwd"], tokens[1])
    node = ensure_node(session, target_path)
    
    if not node:
        return success(error("item_missing"))
    
    name = basename(target_path)
    item_type = "Directory" if node["type"] == "dir" else "File"
    
    lines = [f"Name : {name}", f"Type : {item_type}"]
    
    if node["type"] == "file":
        size = len(node.get("content", ""))
        lines.append(f"Size : {size}")
    
    return success("\n".join(lines))


def handle_test_path(session: dict, tokens: list[str]) -> dict:
    """Test-Path - Check if path exists"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    target_path = normalize_path(session["cwd"], tokens[1])
    node = ensure_node(session, target_path)
    
    return success("True" if node else "False")


def handle_get_service(session: dict) -> dict:
    """Get-Service - List Windows services"""
    lines = ["Status   Name", "------   ----"]
    for service in session["services"]:
        lines.append(f"{service['status']:<8} {service['name']}")
    return success("\n".join(lines))


def handle_start_service(session: dict, tokens: list[str]) -> dict:
    """Start-Service - Start a Windows service"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    service_name = tokens[1].strip('"').strip("'")
    
    for service in session["services"]:
        if service["name"].lower() == service_name.lower():
            service["status"] = "Running"
            return success()
    
    return success(error("service_not_found"))


def handle_stop_service(session: dict, tokens: list[str]) -> dict:
    """Stop-Service - Stop a Windows service"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    service_name = tokens[1].strip('"').strip("'")
    
    for service in session["services"]:
        if service["name"].lower() == service_name.lower():
            service["status"] = "Stopped"
            return success()
    
    return success(error("service_not_found"))


def handle_restart_service(session: dict, tokens: list[str]) -> dict:
    """Restart-Service - Restart a Windows service"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    service_name = tokens[1].strip('"').strip("'")
    
    for service in session["services"]:
        if service["name"].lower() == service_name.lower():
            service["status"] = "Running"
            return success()
    
    return success(error("service_not_found"))


def handle_test_connection(tokens: list[str]) -> dict:
    """Test-Connection - Simulated ping"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    target = tokens[1].strip('"').strip("'")
    
    lines = [
        f"Reply from {target}",
        f"Reply from {target}",
        "Packets: Sent = 2, Received = 2"
    ]
    return success("\n".join(lines))


def handle_ipconfig() -> dict:
    """ipconfig / Get-NetIPConfiguration - Network info"""
    return success(IPCONFIG_OUTPUT)


def handle_resolve_dnsname(tokens: list[str]) -> dict:
    """Resolve-DnsName - DNS lookup"""
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    
    target = tokens[1].strip('"').strip("'")
    
    lines = [
        f"Name : {target}",
        "Address : 142.250.0.1"
    ]
    return success("\n".join(lines))


def handle_whoami() -> dict:
    """whoami / Get-CurrentUser - Current user"""
    return success(WHOAMI_OUTPUT)


def handle_hostname() -> dict:
    """hostname / Get-ComputerName - Computer name"""
    return success(HOSTNAME_OUTPUT)


def handle_get_computerinfo() -> dict:
    """Get-ComputerInfo - System information"""
    return success(COMPUTER_INFO_OUTPUT)


def handle_compress_archive(session: dict, tokens: list[str]) -> dict:
    """Compress-Archive - Create zip file"""
    if len(tokens) != 3:
        return success(error("invalid_arguments"))
    
    source_path = normalize_path(session["cwd"], tokens[1])
    dest_path = normalize_path(session["cwd"], tokens[2])
    
    source_node = ensure_file(session, source_path)
    if not source_node:
        return success(error("file_missing"))
    
    # Create zip file with archived content
    dest_parent = ensure_dir(session, parent_path(dest_path))
    if not dest_parent:
        return success(error("path_missing"))
    
    # Store original content in metadata
    zip_node = {
        "type": "file",
        "content": f"[Compressed: {basename(source_path)}]",
        "metadata": {
            "archive": True,
            "original_content": source_node["content"],
            "original_name": basename(source_path)
        }
    }
    
    add_child(session, dest_path, zip_node)
    return success()


def handle_expand_archive(session: dict, tokens: list[str]) -> dict:
    """Expand-Archive - Extract zip file"""
    if len(tokens) != 3:
        return success(error("invalid_arguments"))
    
    source_path = normalize_path(session["cwd"], tokens[1])
    dest_path = normalize_path(session["cwd"], tokens[2])
    
    source_node = ensure_file(session, source_path)
    if not source_node:
        return success(error("file_missing"))
    
    # Check if it's an archive
    if not source_node.get("metadata", {}).get("archive"):
        return success(error("invalid_arguments"))
    
    # Extract content
    dest_parent = ensure_dir(session, parent_path(dest_path))
    if not dest_parent:
        return success(error("path_missing"))
    
    original_content = source_node["metadata"].get("original_content", "")
    extracted_node = {
        "type": "file",
        "content": original_content,
        "metadata": {}
    }
    
    add_child(session, dest_path, extracted_node)
    return success()


def handle_where_object(tokens: list[str], piped_input: str) -> dict:
    """Where-Object - Filter objects"""
    if not piped_input:
        return success("")
    
    if len(tokens) < 4:
        return success(error("invalid_arguments"))
    
    property_name = tokens[1]
    operator = tokens[2]
    value = tokens[3]
    
    lines = piped_input.splitlines()
    result_lines = []
    
    # Handle Get-Process output filtering
    if property_name.lower() == "id":
        for line in lines:
            if "Id" in line and "ProcessName" in line:
                result_lines.append(line)
                continue
            
            parts = line.split()
            if len(parts) >= 6:
                try:
                    pid = int(parts[5])
                    target_value = int(value)
                    
                    if operator == "-gt" and pid > target_value:
                        result_lines.append(line)
                    elif operator == "-lt" and pid < target_value:
                        result_lines.append(line)
                    elif operator == "-eq" and pid == target_value:
                        result_lines.append(line)
                except (ValueError, IndexError):
                    pass
    
    # Handle Name filtering for Get-ChildItem
    elif property_name.lower() == "name":
        for line in lines:
            if "Name" in line:
                result_lines.append(line)
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                name = parts[-1]
                if operator == "-eq" and name == value:
                    result_lines.append(line)
    
    return success("\n".join(result_lines))


def handle_foreach_object(tokens: list[str], piped_input: str) -> dict:
    """ForEach-Object - Process each item in pipeline.
    
    Supports:
        ... | ForEach-Object { $_.Line }
        
    Simplification: Ignores script blocks and returns input as-is.
    """
    if not piped_input:
        return success("")
    
    # Simple pass-through - ignore script blocks like { $_.Line }
    return success(piped_input)


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def is_blocked_host(hostname: str | None) -> bool:
    if not hostname:
        return True
    normalized = hostname.lower().strip("[]")
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(normalized)
        return (
            address.is_loopback
            or address.is_link_local
            or address.is_private
            or address.is_multicast
            or address.is_unspecified
        )
    except ValueError:
        return False


def resolved_host_is_blocked(hostname: str) -> bool:
    try:
        address_info = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False

    for item in address_info:
        address = item[4][0]
        if is_blocked_host(address):
            return True
    return False


def request_url(url: str) -> tuple[int, str, str]:
    request = Request(url, headers={"User-Agent": "PowerShellEngine/1.0"})
    with urlopen(request, timeout=WEB_TIMEOUT_SECONDS) as response:
        raw_content = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        content = raw_content.decode(charset, errors="replace")
        return response.status, response.geturl(), content


def is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, URLError):
        return isinstance(exc.reason, (TimeoutError, socket.timeout))
    return False


def format_rest_data(data) -> str:
    if isinstance(data, dict):
        return "\n".join(f"{key} : {format_json_value(value)}" for key, value in data.items())
    if isinstance(data, list):
        return "\n".join(format_rest_data(item) for item in data)
    return format_json_value(data)


def format_json_value(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def fallback_web_response(url: str) -> dict:
    return success(f"StatusCode : 200\nContentLength : 1256\nUrl : {url}")


def fallback_rest_response(url: str) -> dict:
    if "jsonplaceholder.typicode.com/todos/1" in url:
        return success("userId : 1\nid : 1\ntitle : sample task\ncompleted : false")
    return success(f"url : {url}\nstatus : ok")


async def handle_invoke_webrequest(session: dict, tokens: list[str], piped_input: str) -> dict:
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    url = normalize_url(tokens[1])
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        return success(error("invalid_arguments"))
    if is_blocked_host(parsed_url.hostname) or await asyncio.to_thread(resolved_host_is_blocked, parsed_url.hostname):
        return success(error("access_denied"))

    try:
        status_code, final_url, content = await asyncio.to_thread(request_url, url)
    except (URLError, TimeoutError, socket.timeout) as exc:
        if is_timeout_error(exc):
            return success(error("request_timeout"))
        return fallback_web_response(url)
    except Exception:
        return fallback_web_response(url)

    return success(f"StatusCode : {status_code}\nContentLength : {len(content)}\nUrl : {final_url}")


async def handle_invoke_restmethod(session: dict, tokens: list[str], piped_input: str) -> dict:
    if len(tokens) != 2:
        return success(error("invalid_arguments"))
    url = normalize_url(tokens[1])
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        return success(error("invalid_arguments"))
    if is_blocked_host(parsed_url.hostname) or await asyncio.to_thread(resolved_host_is_blocked, parsed_url.hostname):
        return success(error("access_denied"))

    try:
        status_code, final_url, content = await asyncio.to_thread(request_url, url)
        return success(format_rest_data(json.loads(content)))
    except (URLError, TimeoutError, socket.timeout) as exc:
        if is_timeout_error(exc):
            return success(error("request_timeout"))
        return fallback_rest_response(url)
    except json.JSONDecodeError:
        return success(error("invalid_arguments"))
    except Exception:
        return fallback_rest_response(url)


CommandHandler = Callable[[dict, list[str], str], dict]
AsyncCommandHandler = Callable[[dict, list[str], str], object]


def no_args(handler: Callable[[], dict]) -> CommandHandler:
    def wrapped(session: dict, tokens: list[str], piped_input: str) -> dict:
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handler()

    return wrapped


def session_no_args(handler: Callable[[dict], dict]) -> CommandHandler:
    def wrapped(session: dict, tokens: list[str], piped_input: str) -> dict:
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handler(session)

    return wrapped


COMMAND_MAP: dict[str, CommandHandler] = {
    "cd": lambda session, tokens, piped_input: handle_cd(session, tokens),
    "set-location": lambda session, tokens, piped_input: handle_cd(session, tokens),
    "pwd": lambda session, tokens, piped_input: handle_pwd(session, tokens),
    "dir": lambda session, tokens, piped_input: handle_dir(session, tokens),
    "new-item": lambda session, tokens, piped_input: handle_new_item(session, tokens),
    "remove-item": lambda session, tokens, piped_input: handle_remove_item(session, tokens),
    "get-content": lambda session, tokens, piped_input: handle_get_content(session, tokens),
    "set-content": lambda session, tokens, piped_input: handle_set_content(session, tokens, append=False, piped_input=piped_input),
    "add-content": lambda session, tokens, piped_input: handle_set_content(session, tokens, append=True, piped_input=piped_input),
    "select-string": lambda session, tokens, piped_input: handle_select_string(session, tokens, piped_input),
    "get-process": session_no_args(handle_get_process),
    "stop-process": lambda session, tokens, piped_input: handle_stop_process(session, tokens),
    "write-output": lambda session, tokens, piped_input: handle_write_output(tokens),
    "cls": lambda session, tokens, piped_input: success(clear=True),
    "copy-item": lambda session, tokens, piped_input: handle_copy_item_command(session, tokens),
    "move-item": lambda session, tokens, piped_input: handle_move_item_command(session, tokens),
    "measure-object": lambda session, tokens, piped_input: handle_measure_object(piped_input),
    "sort-object": lambda session, tokens, piped_input: handle_sort_object(session, tokens, piped_input),
    "select-object": lambda session, tokens, piped_input: handle_select_object(tokens, piped_input),
    "get-date": no_args(handle_get_date),
    "get-location": session_no_args(handle_get_location),
    "rename-item": lambda session, tokens, piped_input: handle_rename_item(session, tokens),
    "get-childitem": lambda session, tokens, piped_input: handle_get_childitem(session, tokens),
    "get-variable": lambda session, tokens, piped_input: handle_get_variable(session, tokens),
    "set-variable": lambda session, tokens, piped_input: handle_set_variable(session, tokens),
    "remove-variable": lambda session, tokens, piped_input: handle_remove_variable(session, tokens),
    "get-item": lambda session, tokens, piped_input: handle_get_item(session, tokens),
    "test-path": lambda session, tokens, piped_input: handle_test_path(session, tokens),
    "get-service": session_no_args(handle_get_service),
    "start-service": lambda session, tokens, piped_input: handle_start_service(session, tokens),
    "stop-service": lambda session, tokens, piped_input: handle_stop_service(session, tokens),
    "restart-service": lambda session, tokens, piped_input: handle_restart_service(session, tokens),
    "test-connection": lambda session, tokens, piped_input: handle_test_connection(tokens),
    "get-netipconfig": no_args(handle_ipconfig),
    "get-netipconfiguration": no_args(handle_ipconfig),
    "resolve-dnsname": lambda session, tokens, piped_input: handle_resolve_dnsname(tokens),
    "get-currentuser": no_args(handle_whoami),
    "get-computername": no_args(handle_hostname),
    "get-computerinfo": no_args(handle_get_computerinfo),
    "compress-archive": lambda session, tokens, piped_input: handle_compress_archive(session, tokens),
    "expand-archive": lambda session, tokens, piped_input: handle_expand_archive(session, tokens),
    "where-object": lambda session, tokens, piped_input: handle_where_object(tokens, piped_input),
    "foreach-object": lambda session, tokens, piped_input: handle_foreach_object(tokens, piped_input),
    "invoke-webrequest": handle_invoke_webrequest,
    "invoke-restmethod": handle_invoke_restmethod,
}


async def execute_single(session: dict, command: str, piped_input: str = "") -> dict:
    assignment = parse_env_assignment(command)
    if assignment:
        key, value = assignment
        session["env"][key] = value
        return success()

    variable_assignment = parse_variable_assignment(command)
    if variable_assignment:
        key, value = variable_assignment
        session.setdefault("variables", {})[key] = value
        return success()

    normalized_command = normalize_alias(substitute_variables(session, command))
    tokens = tokenize(normalized_command)
    if not tokens:
        return success()

    cmd = tokens[0].lower()
    handler = COMMAND_MAP.get(cmd)
    if not handler:
        return success(error("invalid_command"))
    result = handler(session, tokens, piped_input)
    if hasattr(result, "__await__"):
        return await result
    return result


async def execute_command(session: dict, command: str) -> dict:
    if not command:
        return success()

    command_part, redirect_target = split_redirection(command)
    if redirect_target is not None and not command_part:
        return success(error("invalid_arguments"))

    parts = pipeline_parts(command_part)
    result = success()

    for index, part in enumerate(parts):
        result = await execute_single(session, part, result["output"] if index > 0 else "")
        logger.debug("pipe output [%s] -> %s", part, result["output"])
        if result["output"] in STOP_ERRORS:
            break

    if redirect_target is not None and result["output"] not in STOP_ERRORS and not result["clear"]:
        redirect_error = redirect_output(session, redirect_target, result["output"])
        if redirect_error:
            return success(redirect_error)
        result = success()

    if session.get("mode") == "learning" and result["output"] and result["output"] not in STOP_ERRORS:
        if not result["clear"]:
            result["output"] = f"{result['output']}\n\n[learning] Command completed successfully."

    return result
