# PowerShell Engine - Long Session Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Browser                               │
│                                                                      │
│  • WebSocket connection                                             │
│  • Responds to {"type": "ping"} with {"type": "pong"}              │
│  • Stores session_id for reconnection                               │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ WebSocket (ws:// or wss://)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                         NGINX Proxy                                  │
│                                                                      │
│  Configuration (nginx.websocket.conf):                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ proxy_http_version 1.1                                     │    │
│  │ proxy_set_header Upgrade $http_upgrade                     │    │
│  │ proxy_set_header Connection "upgrade"                      │    │
│  │                                                            │    │
│  │ proxy_connect_timeout 300s    (5 minutes)                 │    │
│  │ proxy_read_timeout 7200s      (120 minutes) ◄─────────────┼────┼─ Long session
│  │ proxy_send_timeout 7200s      (120 minutes) ◄─────────────┼────┼─ support
│  │ proxy_buffering off                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ HTTP/WebSocket
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                         Gunicorn                                     │
│                                                                      │
│  Configuration (gunicorn_conf.py + Dockerfile):                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ workers: 4 (CPU * 2 + 1)                                   │    │
│  │ timeout: 7200s           (120 minutes) ◄───────────────────┼────┼─ Worker timeout
│  │ keepalive: 300s          (5 minutes)                       │    │
│  │ worker_class: ProductionUvicornWorker                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  Worker 1   │  │  Worker 2   │  │  Worker 3   │  │  Worker 4   ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│
└─────────┼────────────────┼────────────────┼────────────────┼────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    Uvicorn Worker (per worker)                       │
│                                                                      │
│  Configuration (gunicorn_worker.py):                                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ loop: uvloop                                               │    │
│  │ http: httptools                                            │    │
│  │ ws: websockets                                             │    │
│  │                                                            │    │
│  │ ws_ping_interval: 30s    ◄─────────────────────────────────┼────┼─ Keep-alive ping
│  │ ws_ping_timeout: 300s    (5 minutes)                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ ASGI
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Application                             │
│                           (main.py)                                  │
│                                                                      │
│  WebSocket Endpoint: /terminal                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                                                            │    │
│  │  Connection Flow:                                          │    │
│  │  1. Accept WebSocket connection                            │    │
│  │  2. Get or create session (session_id)                     │    │
│  │  3. Send {"type": "init"} with session_id                  │    │
│  │  4. Start heartbeat loop                                   │    │
│  │  5. Process commands                                       │    │
│  │                                                            │    │
│  │  Heartbeat Configuration:                                  │    │
│  │  • HEARTBEAT_INTERVAL: 30s  ◄──────────────────────────────┼────┼─ App-level ping
│  │  • HEARTBEAT_TIMEOUT: 300s  (5 minutes)                    │    │
│  │                                                            │    │
│  │  Heartbeat Loop:                                           │    │
│  │  ┌──────────────────────────────────────────────────┐     │    │
│  │  │ while not stopped:                               │     │    │
│  │  │   await sleep(30s)                               │     │    │
│  │  │   if idle > 300s:                                │     │    │
│  │  │     close_connection()                           │     │    │
│  │  │   send({"type": "ping"})                         │     │    │
│  │  └──────────────────────────────────────────────────┘     │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Function calls
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      Session Manager                                 │
│                    (session_manager.py)                              │
│                                                                      │
│  Configuration:                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ SESSION_TTL_SECONDS: 7200s  (120 minutes) ◄────────────────┼────┼─ Session lifetime
│  │                                                            │    │
│  │ Session Storage: _sessions = {}                            │    │
│  │                                                            │    │
│  │ Session Structure:                                         │    │
│  │ {                                                          │    │
│  │   "session_id": "abc123...",                               │    │
│  │   "cwd": "C:\\Users\\User",                                │    │
│  │   "fs": {...},                                             │    │
│  │   "history": [...],                                        │    │
│  │   "env": {...},                                            │    │
│  │   "variables": {...},                                      │    │
│  │   "processes": [...],                                      │    │
│  │   "services": [...],                                       │    │
│  │   "created_at": 1234567890,                                │    │
│  │   "last_seen": 1234567890  ◄─ Updated on activity         │    │
│  │ }                                                          │    │
│  │                                                            │    │
│  │ Cleanup Task (runs every 5 minutes):                       │    │
│  │ ┌────────────────────────────────────────────────────┐    │    │
│  │ │ while True:                                        │    │    │
│  │ │   await sleep(300s)                                │    │    │
│  │ │   cutoff = now - 7200s                             │    │    │
│  │ │   remove sessions where last_seen < cutoff         │    │    │
│  │ └────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Function calls
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Execution Engine                                 │
│                   (execution_engine.py)                              │
│                                                                      │
│  • Parses PowerShell commands                                       │
│  • Executes commands (New-Item, Set-Location, etc.)                │
│  • Manages virtual filesystem                                       │
│  • Handles pipelines                                                │
│  • Returns command output                                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Timeout Flow Diagram

```
Time: 0s
┌─────────────────────────────────────────────────────────────┐
│ Client connects to WebSocket                                 │
│ • NGINX: proxy_connect_timeout = 300s                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
Time: 0-30s
┌─────────────────────────────────────────────────────────────┐
│ Connection established                                       │
│ • Session created with TTL = 7200s                          │
│ • Heartbeat loop started                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
Time: 30s, 60s, 90s, ... (every 30 seconds)
┌─────────────────────────────────────────────────────────────┐
│ Server sends {"type": "ping"}                               │
│ • Uvicorn: ws_ping_interval = 30s                           │
│ • FastAPI: HEARTBEAT_INTERVAL = 30s                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
Time: 0-300s (if no activity)
┌─────────────────────────────────────────────────────────────┐
│ WebSocket idle timeout check                                │
│ • If no activity for 300s → close connection                │
│ • Uvicorn: ws_ping_timeout = 300s                           │
│ • FastAPI: HEARTBEAT_TIMEOUT = 300s                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
Time: 0-7200s (session active)
┌─────────────────────────────────────────────────────────────┐
│ Session remains active                                       │
│ • User can execute commands                                  │
│ • Each activity updates last_seen                            │
│ • NGINX: proxy_read_timeout = 7200s                         │
│ • NGINX: proxy_send_timeout = 7200s                         │
│ • Gunicorn: timeout = 7200s                                 │
│ • Session: TTL = 7200s                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
Time: 7200s+ (no activity)
┌─────────────────────────────────────────────────────────────┐
│ Session cleanup                                              │
│ • Background task runs every 300s                            │
│ • Removes sessions where (now - last_seen) > 7200s          │
│ • Frees memory and resources                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Heartbeat Sequence Diagram

```
Client                  FastAPI                 Session
  │                       │                       │
  │──── Connect ─────────>│                       │
  │                       │                       │
  │                       │─── Create/Get ───────>│
  │                       │<──── Session ─────────│
  │                       │                       │
  │<─── {"type":"init"} ──│                       │
  │                       │                       │
  │                       │                       │
  │                    [30s later]                │
  │                       │                       │
  │<─── {"type":"ping"} ──│                       │
  │                       │                       │
  │──── {"type":"pong"} ─>│                       │
  │                       │─── touch_session() ──>│
  │                       │                       │
  │                       │                       │
  │                    [30s later]                │
  │                       │                       │
  │<─── {"type":"ping"} ──│                       │
  │                       │                       │
  │──── {"type":"pong"} ─>│                       │
  │                       │─── touch_session() ──>│
  │                       │                       │
  │                       │                       │
  │  [User executes command]                      │
  │                       │                       │
  │─ {"type":"command"} ─>│                       │
  │                       │─── touch_session() ──>│
  │                       │                       │
  │                       │─── execute_command() ─>
  │                       │                       │
  │<─ {"type":"response"} │                       │
  │                       │                       │
  │                       │                       │
  │  [Continues for up to 120 minutes]            │
  │                       │                       │
```

---

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Created                           │
│                                                              │
│  • session_id generated                                     │
│  • created_at = now                                         │
│  • last_seen = now                                          │
│  • TTL = 7200s                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Active Session                              │
│                                                              │
│  • User executes commands                                   │
│  • last_seen updated on each activity                       │
│  • Heartbeat keeps connection alive                         │
│  • Session data persists in memory                          │
│                                                              │
│  Duration: 0 - 7200 seconds                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                  [Decision Point]
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌────────────────┐
│  Activity?    │            │  No Activity   │
│               │            │  for 7200s     │
│  Yes          │            │                │
│  │            │            │  ▼             │
│  └─> Update   │            │  Cleanup       │
│      last_seen│            │  Task          │
│      │        │            │  │             │
│      └────────┼────────────┼──┘             │
│               │            │                │
│  Loop back to │            │  ▼             │
│  Active       │            │  Session       │
│               │            │  Deleted       │
└───────────────┘            └────────────────┘
```

---

## Configuration Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: NGINX                            │
│                                                              │
│  • First line of defense                                    │
│  • Handles SSL/TLS termination                              │
│  • Proxy timeouts: 7200s                                    │
│  • Connection timeout: 300s                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: Gunicorn                         │
│                                                              │
│  • Process manager                                          │
│  • Worker timeout: 7200s                                    │
│  • Keep-alive: 300s                                         │
│  • Manages multiple workers                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Uvicorn                          │
│                                                              │
│  • ASGI server                                              │
│  • WebSocket ping: 30s interval                             │
│  • WebSocket timeout: 300s                                  │
│  • Handles WebSocket protocol                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: FastAPI                          │
│                                                              │
│  • Application logic                                        │
│  • Heartbeat: 30s interval                                  │
│  • Idle timeout: 300s                                       │
│  • Command execution                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 5: Session                          │
│                                                              │
│  • Data persistence                                         │
│  • Session TTL: 7200s                                       │
│  • Cleanup every 300s                                       │
│  • In-memory storage                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture ensures:
- ✅ 120-minute session support at all layers
- ✅ Redundant keep-alive mechanisms
- ✅ Graceful degradation
- ✅ Automatic cleanup
- ✅ Production-ready reliability
