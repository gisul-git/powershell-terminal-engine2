import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from execution_engine import build_terminal_history, execute_command
from session_manager import create_session, delete_session, generate_prompt


app = FastAPI(title="PowerShell Simulation")
logger = logging.getLogger(__name__)


@app.websocket("/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    """
    PowerShell WebSocket terminal endpoint.
    Matches Linux bash engine behavior for stability and robustness.
    """
    origin = websocket.headers.get("origin", "")
    print(f"Origin: {origin}")

    # Production traffic is terminated by nginx, so allow browser WebSocket
    # requests from the configured public domains instead of rejecting by Origin.
    await websocket.accept()
    print("Accepted WebSocket")
    
    session = create_session()
    session_id = id(session)
    
    # Send INIT message immediately on connection
    await websocket.send_json(
        {
            "type": "init",
            "data": {
                "banner": "Windows PowerShell Simulation\n\n",
                "prompt": generate_prompt(session),
            },
        }
    )
    print("INIT message sent")

    try:
        while True:
            # Safe message handling - catch invalid JSON/format
            try:
                message = await websocket.receive_json()
                print(f"Received: {message}")
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Invalid message format: {e}")
                await websocket.send_json(
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
                print("Ignoring resize message")
                continue
            
            if message_type == "ping":
                print("Ignoring ping message")
                continue

            # Handle command execution
            if message_type == "command":
                command = str(message.get("data", "")).strip()
                
                # Handle special \submit command
                if command == "\\submit":
                    await asyncio.sleep(0.1)
                    await websocket.send_json(
                        {
                            "type": "response",
                            "data": {
                                "output": build_terminal_history(session),
                                "prompt": generate_prompt(session),
                            },
                        }
                    )
                    print("Sending response: submit history")
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
                    
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": response_data,
                    }
                )
                print("Sending response: command executed")
                continue

            # Handle submit message type
            if message_type == "submit":
                await asyncio.sleep(0.1)
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": {
                            "output": build_terminal_history(session),
                            "prompt": generate_prompt(session),
                        },
                    }
                )
                print("Sending response: submit history")
                continue

            # Unsupported message type
            print(f"Unsupported message type: {message_type}")
            await websocket.send_json(
                {
                    "type": "response",
                    "data": {
                        "output": f"Unsupported message type: {message_type}",
                        "prompt": generate_prompt(session),
                    },
                }
            )
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        delete_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        delete_session(session_id)
        try:
            await websocket.close()
        except Exception:
            pass
