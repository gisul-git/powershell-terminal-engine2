import asyncio
import contextlib
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from execution_engine import build_terminal_history, execute_command
from session_manager import (
    SESSION_TTL_SECONDS,
    cleanup_idle_sessions,
    generate_prompt,
    get_or_create_session,
    touch_session,
)


app = FastAPI(title="PowerShell Simulation")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARNING").upper())
logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 20
HEARTBEAT_TIMEOUT_SECONDS = 120


async def cleanup_sessions_forever() -> None:
    while True:
        await asyncio.sleep(300)
        removed_count = cleanup_idle_sessions(SESSION_TTL_SECONDS)
        if removed_count:
            logger.debug("Cleaned up %s idle sessions", removed_count)


@app.on_event("startup")
async def start_background_tasks() -> None:
    app.state.session_cleanup_task = asyncio.create_task(cleanup_sessions_forever())


@app.on_event("shutdown")
async def stop_background_tasks() -> None:
    task = getattr(app.state, "session_cleanup_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def send_json(websocket: WebSocket, send_lock: asyncio.Lock, payload: dict) -> None:
    async with send_lock:
        await websocket.send_json(payload)


async def heartbeat_loop(
    websocket: WebSocket,
    send_lock: asyncio.Lock,
    session: dict,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        if stop_event.is_set():
            return

        idle_for = asyncio.get_running_loop().time() - session.get("last_ws_seen", 0)
        if idle_for > HEARTBEAT_TIMEOUT_SECONDS:
            logger.debug("Closing idle websocket for session %s", session["session_id"])
            await websocket.close(code=1001)
            return

        await send_json(websocket, send_lock, {"type": "ping"})


@app.websocket("/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    """
    PowerShell WebSocket terminal endpoint.
    Matches Linux bash engine behavior for stability and robustness.
    """
    origin = websocket.headers.get("origin", "")
    logger.debug("WebSocket origin: %s", origin)

    # Production traffic is terminated by nginx, so allow browser WebSocket
    # requests from the configured public domains instead of rejecting by Origin.
    await websocket.accept()
    requested_session_id = websocket.query_params.get("session_id") or websocket.query_params.get("token")
    session = get_or_create_session(requested_session_id)
    session["last_ws_seen"] = asyncio.get_running_loop().time()
    session_id = session["session_id"]
    send_lock = asyncio.Lock()
    stop_event = asyncio.Event()
    heartbeat_task = asyncio.create_task(heartbeat_loop(websocket, send_lock, session, stop_event))
    
    # Send INIT immediately. Heavy data stays lazy so first paint is fast.
    await send_json(
        websocket,
        send_lock,
        {
            "type": "init",
            "data": {
                "session_id": session_id,
                "prompt": generate_prompt(session),
            },
        },
    )

    try:
        while True:
            # Safe message handling - catch invalid JSON/format
            try:
                message = await websocket.receive_json()
                session["last_ws_seen"] = asyncio.get_running_loop().time()
                touch_session(session)
                logger.debug("Received websocket message type: %s", message.get("type"))
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.warning("Invalid message format: %s", e)
                await send_json(
                    websocket,
                    send_lock,
                    {
                        "type": "response",
                        "data": {
                            "output": "Invalid input format",
                            "prompt": generate_prompt(session),
                        },
                    }
                )
                continue

            message_type = message.get("type")
            
            # Ignore unsupported message types (resize, ping)
            if message_type == "resize":
                continue
            
            if message_type == "ping":
                await send_json(websocket, send_lock, {"type": "pong"})
                continue

            if message_type == "pong":
                continue

            # Handle command execution
            if message_type == "command":
                command = str(message.get("data", "")).strip()
                
                # Handle special \submit command
                if command == "\\submit":
                    await send_json(
                        websocket,
                        send_lock,
                        {
                            "type": "response",
                            "data": {
                                "output": build_terminal_history(session),
                                "prompt": generate_prompt(session),
                            },
                        },
                    )
                    continue
                
                # Execute command
                prompt_before = generate_prompt(session)
                result = await execute_command(session, command)
                prompt_after = generate_prompt(session)
                
                # Store in history
                session["history"].append(
                    {
                        "prompt": prompt_before,
                        "command": command,
                        "output": result["output"],
                    }
                )
                
                # Send response
                response_data = {
                    "output": result["output"],
                    "prompt": prompt_after,
                }
                if result.get("clear"):
                    response_data["clear"] = True
                    
                await send_json(
                    websocket,
                    send_lock,
                    {
                        "type": "response",
                        "data": response_data,
                    },
                )
                continue

            # Handle submit message type
            if message_type == "submit":
                await send_json(
                    websocket,
                    send_lock,
                    {
                        "type": "response",
                        "data": {
                            "output": build_terminal_history(session),
                            "prompt": generate_prompt(session),
                        },
                    },
                )
                continue

            # Unsupported message type
            logger.debug("Unsupported message type: %s", message_type)
            await send_json(
                websocket,
                send_lock,
                {
                    "type": "response",
                    "data": {
                        "output": f"Unsupported message type: {message_type}",
                        "prompt": generate_prompt(session),
                    },
                }
            )
            
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected for session %s", session_id)
    except Exception as e:
        logger.exception("WebSocket error for session %s: %s", session_id, e)
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        stop_event.set()
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
