from typing import Iterable


ERRORS = {
    "invalid_command": "Invalid command",
    "invalid_arguments": "Invalid arguments",
    "missing_destination": "Missing destination path",
    "path_missing": "Path does not exist",
    "file_missing": "File not found",
    "source_missing": "Source file not found",
    "item_missing": "Item not found",
    "access_denied": "Access denied",
    "cannot_remove_directory": "Cannot remove directory",
    "cannot_move_file": "Cannot move file",
    "same_file": "Cannot overwrite same file",
    "service_not_found": "Service not found",
    "variable_not_found": "variable not found",
    "request_timeout": "Request timeout",
}


def error(message_key: str) -> str:
    return ERRORS[message_key]


def has_flag(tokens: Iterable[str], flag: str) -> bool:
    return any(token.lower() == flag.lower() for token in tokens)


def validate_flags(tokens: Iterable[str], allowed_flags: set[str]) -> bool:
    normalized = {flag.lower() for flag in allowed_flags}
    for token in tokens:
        if token.startswith("-") and token.lower() not in normalized:
            return False
    return True
