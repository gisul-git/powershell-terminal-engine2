from copy import deepcopy

from path_resolver import HOME_PATH, ROOT_PATH


DEFAULT_PROCESSES = [
    {"pid": 101, "name": "powershell"},
    {"pid": 102, "name": "node"},
]

DEFAULT_SERVICES = [
    {"name": "Spooler", "status": "Running"},
    {"name": "WinDefend", "status": "Running"},
    {"name": "WSearch", "status": "Stopped"},
]

# Session storage for cleanup
_sessions = {}


def create_session() -> dict:
    cwd = HOME_PATH
    session = {
        "cwd": cwd,
        "fs": {
            ROOT_PATH: {
                "type": "dir",
                "children": {"Users": r"C:\Users"},
            },
            r"C:\Users": {
                "type": "dir",
                "children": {"User": HOME_PATH},
            },
            cwd: {
                "type": "dir",
                "children": {},
            }
        },
        "history": [],
        "env": {},
        "processes": deepcopy(DEFAULT_PROCESSES),
        "services": deepcopy(DEFAULT_SERVICES),
        "mode": "exam",
    }
    _sessions[id(session)] = session
    return session


def delete_session(session_id: int) -> None:
    """Clean up session on disconnect"""
    _sessions.pop(session_id, None)


def generate_prompt(session: dict) -> str:
    return f"PS {session['cwd']}> "
