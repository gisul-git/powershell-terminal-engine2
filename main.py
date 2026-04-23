import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from execution_engine import build_terminal_history, execute_command
from session_manager import create_session, generate_prompt


app = FastAPI(title="PowerShell Simulation")


@app.websocket("/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session = create_session()

    await websocket.send_json(
        {
            "type": "init",
            "data": {
                "banner": "Windows PowerShell Simulation\n\n",
                "prompt": generate_prompt(session),
            },
        }
    )

    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")

            if message_type == "command":
                command = str(message.get("data", "")).strip()
                if command == "\\submit":
                    await asyncio.sleep(0.1)
                    await websocket.send_json(
                        {
                            "type": "response",
                            "data": {
                                "output": build_terminal_history(session),
                                "prompt": generate_prompt(session),
                                "clear": False,
                            },
                        }
                    )
                    continue
                prompt_before = generate_prompt(session)
                result = await execute_command(session, command)
                prompt_after = generate_prompt(session)
                session["history"].append(
                    {
                        "prompt": prompt_before,
                        "command": command,
                        "output": result["output"],
                    }
                )
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": {
                            "output": result["output"],
                            "prompt": prompt_after,
                            "clear": result["clear"],
                        },
                    }
                )
            elif message_type == "submit":
                await asyncio.sleep(0.1)
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": {
                            "output": build_terminal_history(session),
                            "prompt": generate_prompt(session),
                            "clear": False,
                        },
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": {
                            "output": "Invalid input",
                            "prompt": generate_prompt(session),
                            "clear": False,
                        },
                    }
                )
    except WebSocketDisconnect:
        return
