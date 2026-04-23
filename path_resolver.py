import ntpath


ROOT_PATH = "C:\\"
HOME_PATH = r"C:\Users\User"


def strip_quotes(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().strip('"').strip("'")


def normalize_path(cwd: str, raw_path: str | None) -> str:
    candidate = strip_quotes(raw_path)
    if not candidate or candidate == ".":
        return cwd
    if candidate == "~":
        return HOME_PATH
    if candidate == "\\":
        return ROOT_PATH

    candidate = candidate.replace("/", "\\")

    if candidate.startswith("\\") and not candidate.startswith("\\\\"):
        return ntpath.normpath(f"C:{candidate}")

    if ntpath.splitdrive(candidate)[0]:
        normalized = ntpath.normpath(candidate)
    else:
        normalized = ntpath.normpath(ntpath.join(cwd, candidate))

    if normalized in {".", ""}:
        return cwd

    drive, tail = ntpath.splitdrive(normalized)
    if not drive:
        drive = "C:"
    if not tail.startswith("\\"):
        tail = f"\\{tail}" if tail else "\\"
    return ntpath.normpath(f"{drive}{tail}")


def parent_path(path: str) -> str:
    normalized = ntpath.normpath(path)
    drive, tail = ntpath.splitdrive(normalized)
    if not drive:
        drive = "C:"
    if tail in {"", "\\"}:
        return ROOT_PATH
    parent = ntpath.dirname(normalized)
    return ntpath.normpath(parent or ROOT_PATH)


def basename(path: str) -> str:
    normalized = ntpath.normpath(path)
    if normalized == ROOT_PATH:
        return ROOT_PATH
    return ntpath.basename(normalized)
