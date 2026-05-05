# Timeout Configuration Quick Reference

## All Timeout Values at a Glance

| Component | Setting | Value | Purpose |
|-----------|---------|-------|---------|
| **Session Manager** | SESSION_TTL_SECONDS | 7200s (120 min) | Session lifetime |
| **Gunicorn** | timeout | 7200s (120 min) | Worker timeout |
| **Gunicorn** | keepalive | 300s (5 min) | Keep-alive |
| **Uvicorn Worker** | ws_ping_interval | 30s | WebSocket ping frequency |
| **Uvicorn Worker** | ws_ping_timeout | 300s (5 min) | WebSocket ping timeout |
| **FastAPI** | HEARTBEAT_INTERVAL | 30s | Application ping frequency |
| **FastAPI** | HEARTBEAT_TIMEOUT | 300s (5 min) | Application idle timeout |
| **NGINX** | proxy_connect_timeout | 300s (5 min) | Connection establishment |
| **NGINX** | proxy_read_timeout | 7200s (120 min) | Read timeout |
| **NGINX** | proxy_send_timeout | 7200s (120 min) | Send timeout |

---

## Files Modified

### 1. `Dockerfile`
```dockerfile
CMD ["gunicorn", "-k", "gunicorn_worker.ProductionUvicornWorker", "-c", "gunicorn_conf.py", "main:app", "--timeout", "7200", "--keep-alive", "300"]
```

### 2. `gunicorn_conf.py`
```python
timeout = int(os.getenv("GUNICORN_TIMEOUT", "7200"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "300"))
```

### 3. `gunicorn_worker.py`
```python
CONFIG_KWARGS = {
    "ws_ping_interval": 30,
    "ws_ping_timeout": 300,
}
```

### 4. `session_manager.py`
```python
SESSION_TTL_SECONDS = 7200
```

### 5. `main.py`
```python
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_SECONDS = 300
```

### 6. `nginx.websocket.conf`
```nginx
proxy_connect_timeout 300;
proxy_read_timeout 7200;
proxy_send_timeout 7200;
proxy_buffering off;
```

---

## Testing

```bash
# Run configuration tests
python test_long_session.py

# Expected output: 8 passed, 0 failed
```

---

## Deployment Checklist

- [ ] Build Docker image with updated Dockerfile
- [ ] Update NGINX configuration
- [ ] Restart NGINX service
- [ ] Deploy new container
- [ ] Verify WebSocket connections
- [ ] Monitor session duration
- [ ] Check logs for errors

---

## Quick Verification

```bash
# Check Dockerfile
grep "timeout" Dockerfile

# Check gunicorn config
grep "timeout\|keepalive" gunicorn_conf.py

# Check session TTL
grep "SESSION_TTL_SECONDS" session_manager.py

# Check heartbeat
grep "HEARTBEAT" main.py

# Check NGINX
grep "proxy_.*_timeout" nginx.websocket.conf
```

---

## Rollback Plan

If issues occur, revert to previous values:

| Setting | Previous | New |
|---------|----------|-----|
| Gunicorn timeout | 3600s | 7200s |
| Gunicorn keepalive | 120s | 300s |
| WebSocket ping interval | 20s | 30s |
| WebSocket ping timeout | 120s | 300s |
| Heartbeat interval | 20s | 30s |
| Heartbeat timeout | 120s | 300s |
| NGINX read timeout | 3600s | 7200s |
| NGINX send timeout | 3600s | 7200s |

---

## Support

For issues or questions:
1. Check logs: `docker logs <container_id>`
2. Run tests: `python test_long_session.py`
3. Review documentation: `LONG_SESSION_CONFIGURATION.md`
