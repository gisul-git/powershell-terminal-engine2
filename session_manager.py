from copy import deepcopy

from path_resolver import HOME_PATH, ROOT_PATH


DEFAULT_PROCESSES = [
    {"pid": 101, "name": "powershell"},
    {"pid": 102, "name": "node"},
]


def create_session() -> dict:
    cwd = HOME_PATH
    return {
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
        "mode": "exam",
    }


def generate_prompt(session: dict) -> str:
    return f"PS {session['cwd']}> "
