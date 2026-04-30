import time
from copy import deepcopy
from uuid import uuid4

from path_resolver import HOME_PATH, ROOT_PATH


SESSION_TTL_SECONDS = 2 * 60 * 60

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


def create_session(session_id: str | None = None) -> dict:
    cwd = HOME_PATH
    now = time.time()
    resolved_session_id = session_id or uuid4().hex
    session = {
        "session_id": resolved_session_id,
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
        "variables": {},
        "processes": deepcopy(DEFAULT_PROCESSES),
        "services": deepcopy(DEFAULT_SERVICES),
        "mode": "exam",
        "created_at": now,
        "last_seen": now,
    }
    _sessions[resolved_session_id] = session
    return session


def get_session(session_id: str) -> dict | None:
    session = _sessions.get(session_id)
    if session:
        touch_session(session)
    return session


def get_or_create_session(session_id: str | None = None) -> dict:
    if session_id:
        session = get_session(session_id)
        if session:
            return session
    return create_session(session_id)


def touch_session(session: dict) -> None:
    session["last_seen"] = time.time()


def cleanup_idle_sessions(max_idle_seconds: int = SESSION_TTL_SECONDS) -> int:
    cutoff = time.time() - max_idle_seconds
    stale_ids = [
        session_id
        for session_id, session in _sessions.items()
        if session.get("last_seen", 0) < cutoff
    ]
    for session_id in stale_ids:
        _sessions.pop(session_id, None)
    return len(stale_ids)


def delete_session(session_id: str) -> None:
    """Force-delete a session."""
    _sessions.pop(session_id, None)


def generate_prompt(session: dict) -> str:
    return f"PS {session['cwd']}> "
