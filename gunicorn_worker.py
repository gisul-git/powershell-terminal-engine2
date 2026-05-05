from uvicorn.workers import UvicornWorker


class ProductionUvicornWorker(UvicornWorker):
    """
    Production Uvicorn worker optimized for long-running WebSocket sessions.
    Supports sessions up to 120 minutes (7200 seconds).
    """
    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "ws": "websockets",
        "ws_ping_interval": 30,  # Send WebSocket ping every 30 seconds
        "ws_ping_timeout": 300,  # 5 minutes timeout for ping response
    }
