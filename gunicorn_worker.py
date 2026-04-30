from uvicorn.workers import UvicornWorker


class ProductionUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "ws": "websockets",
        "ws_ping_interval": 20,
        "ws_ping_timeout": 120,
    }
