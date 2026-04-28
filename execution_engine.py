import asyncio
import logging
import random
import shlex
from copy import deepcopy
from typing import Iterable

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
}


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


def parse_env_assignment(command: str) -> tuple[str, str] | None:
    if not command.startswith("$env:") or "=" not in command:
        return None
    left, right = command.split("=", 1)
    key = left[5:].strip()
    value = right.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


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


def handle_new_item(session: dict, tokens: list[str]) -> dict:
    if not validate_flags(tokens[1:], {"-ItemType"}):
        return success(error("invalid_arguments"))

    path_token = None
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token.lower() == "-itemtype":
            index += 2
            continue
        if token.startswith("-"):
            return success(error("invalid_arguments"))
        if path_token is not None:
            return success(error("invalid_arguments"))
        path_token = token
        index += 1

    item_type = get_option(tokens, "-ItemType")
    if not path_token or not item_type:
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


def handle_set_content(session: dict, tokens: list[str], append: bool) -> dict:
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
    if len(tokens) < 2:
        return success(error("invalid_arguments"))

    if len(tokens) == 2:
        return success(select_string(piped_input, tokens[1].strip('"').strip("'")))

    possible_path = normalize_path(session["cwd"], tokens[1])
    if ensure_node(session, possible_path):
        read_error, content = read_content(session, possible_path)
        if read_error:
            return success(read_error)
        pattern = " ".join(tokens[2:]).strip('"').strip("'")
        if not pattern:
            return success(error("invalid_arguments"))
        return success(select_string(content, pattern))

    pattern = " ".join(tokens[1:]).strip('"').strip("'")
    return success(select_string(piped_input, pattern))


def handle_get_process(session: dict) -> dict:
    lines = ["Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  ProcessName"]
    for process in session["processes"]:
        lines.append(f"{12:>7} {4:>7} {24:>8} {18:>10} {0.15:>10.2f} {process['pid']:>6}  {process['name']}")
    return success("\n".join(lines))


def handle_stop_process(session: dict, tokens: list[str]) -> dict:
    if len(tokens) == 2 and tokens[1].isdigit():
        pid = tokens[1]
    else:
        if not validate_flags(tokens[1:], {"-Id"}):
            return success(error("invalid_arguments"))
        pid = get_option(tokens, "-Id")
    if not pid or not pid.isdigit():
        return success(error("invalid_arguments"))
    for process in session["processes"]:
        if process["pid"] == int(pid):
            session["processes"] = [item for item in session["processes"] if item["pid"] != int(pid)]
            return success()
    return success(error("item_missing"))


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
    lines = [
        "IPv4 Address . . . . . : 192.168.1.10",
        "Subnet Mask . . . . . : 255.255.255.0",
        "Gateway . . . . . . . : 192.168.1.1"
    ]
    return success("\n".join(lines))


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
    return success("User")


def handle_hostname() -> dict:
    """hostname / Get-ComputerName - Computer name"""
    return success("WIN-SERVER01")


def handle_get_computerinfo() -> dict:
    """Get-ComputerInfo - System information"""
    lines = [
        "OSName : Windows Server",
        "OSVersion : 2022",
        "ComputerName : WIN-SERVER01"
    ]
    return success("\n".join(lines))


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


def handle_foreach_object(piped_input: str) -> dict:
    """ForEach-Object - Process each item"""
    if not piped_input:
        return success("")
    
    # Simple pass-through implementation
    return success(piped_input)


def execute_single(session: dict, command: str, piped_input: str = "") -> dict:
    assignment = parse_env_assignment(command)
    if assignment:
        key, value = assignment
        session["env"][key] = value
        return success()

    normalized_command = normalize_alias(command)
    tokens = tokenize(normalized_command)
    if not tokens:
        return success()

    cmd = tokens[0].lower()

    if cmd == "cd":
        return handle_cd(session, tokens)
    if cmd == "pwd":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return success(session["cwd"])
    if cmd == "dir":
        return handle_dir(session, tokens)
    if cmd == "new-item":
        return handle_new_item(session, tokens)
    if cmd == "remove-item":
        return handle_remove_item(session, tokens)
    if cmd == "get-content":
        return handle_get_content(session, tokens)
    if cmd == "set-content":
        return handle_set_content(session, tokens, append=False)
    if cmd == "add-content":
        return handle_set_content(session, tokens, append=True)
    if cmd == "select-string":
        return handle_select_string(session, tokens, piped_input)
    if cmd == "get-process":
        return handle_get_process(session)
    if cmd == "stop-process":
        return handle_stop_process(session, tokens)
    if cmd == "write-output":
        return success(" ".join(tokens[1:]).strip('"').strip("'"))
    if cmd == "cls":
        return success(clear=True)
    if cmd == "copy-item":
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
    if cmd == "move-item":
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
    if cmd == "measure-object":
        return handle_measure_object(piped_input)
    if cmd == "sort-object":
        return handle_sort_object(session, tokens, piped_input)
    if cmd == "select-object":
        return handle_select_object(tokens, piped_input)
    if cmd == "get-date":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_get_date()
    if cmd == "get-location":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_get_location(session)
    if cmd == "rename-item":
        return handle_rename_item(session, tokens)
    if cmd == "get-childitem":
        return handle_get_childitem(session, tokens)
    if cmd == "get-item":
        return handle_get_item(session, tokens)
    if cmd == "test-path":
        return handle_test_path(session, tokens)
    if cmd == "get-service":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_get_service(session)
    if cmd == "start-service":
        return handle_start_service(session, tokens)
    if cmd == "stop-service":
        return handle_stop_service(session, tokens)
    if cmd == "restart-service":
        return handle_restart_service(session, tokens)
    if cmd == "test-connection":
        return handle_test_connection(tokens)
    if cmd == "get-netipconfig" or cmd == "get-netipconfiguration":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_ipconfig()
    if cmd == "resolve-dnsname":
        return handle_resolve_dnsname(tokens)
    if cmd == "get-currentuser":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_whoami()
    if cmd == "get-computername":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_hostname()
    if cmd == "get-computerinfo":
        if len(tokens) != 1:
            return success(error("invalid_arguments"))
        return handle_get_computerinfo()
    if cmd == "compress-archive":
        return handle_compress_archive(session, tokens)
    if cmd == "expand-archive":
        return handle_expand_archive(session, tokens)
    if cmd == "where-object":
        return handle_where_object(tokens, piped_input)
    if cmd == "foreach-object":
        return handle_foreach_object(piped_input)
    return success(error("invalid_command"))


async def execute_command(session: dict, command: str) -> dict:
    await asyncio.sleep(random.uniform(0.1, 0.3))

    if not command:
        return success()

    command_part, redirect_target = split_redirection(command)
    if redirect_target is not None and not command_part:
        return success(error("invalid_arguments"))

    parts = pipeline_parts(command_part)
    result = success()

    for index, part in enumerate(parts):
        result = execute_single(session, part, result["output"] if index > 0 else "")
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
