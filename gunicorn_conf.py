import multiprocessing
import os


bind = os.getenv("BIND", "0.0.0.0:4042")
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "7200"))  # 120 minutes for long sessions
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "300"))  # 5 minutes keep-alive
loglevel = os.getenv("LOG_LEVEL", "warning").lower()
accesslog = "-"
errorlog = "-"
