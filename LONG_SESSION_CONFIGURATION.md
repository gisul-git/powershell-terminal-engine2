# Long-Running Session Configuration

## Overview

The PowerShell WebSocket terminal engine has been optimized to support **long-running sessions up to 120 minutes (7200 seconds)**. This prevents WebSocket disconnections during extended user tests and ensures stable connections.

---

## Configuration Changes

### 1. Docker Configuration (`Dockerfile`)

**Updated CMD with explicit timeout parameters:**

```dockerfile
CMD ["gunicorn", "-k", "gunicorn_worker.ProductionUvicornWorker", "-c", "gunicorn_conf.py", "main:app", "--timeout", "7200", "--keep-alive", "300"]
```

**Changes:**
- `--timeout 7200`: Worker timeout set to 120 minutes
- `--keep-alive 300`: Keep-alive connections for 5 minutes

---

### 2. Gunicorn Configuration (`gunicorn_conf.py`)

**Updated default timeouts:**

```python
timeout = int(os.getenv("GUNICORN_TIMEOUT", "7200"))  # 120 minutes
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "300"))  # 5 minutes
```

**Purpose:**
- Prevents Gunicorn from killing workers during long sessions
- Maintains persistent connections

---

### 3. Uvicorn Worker Configuration (`gunicorn_worker.py`)

**Updated WebSocket ping settings:**

```python
CONFIG_KWARGS = {
    "loop": "uvloop",
    "http": "httptools",
    "ws": "websockets",
    "ws_ping_interval": 30,  # Send ping every 30 seconds
    "ws_ping_timeout": 300,  # 5 minutes timeout for ping response
}
```

**Purpose:**
- Keeps WebSocket connections alive with regular pings
- Detects dead connections within 5 minutes

---

### 4. Session Manager (`session_manager.py`)

**Updated session TTL:**

```python
SESSION_TTL_SECONDS = 7200  # 120 minutes (2 hours)
```

**Purpose:**
- Sessions remain active for 120 minutes of inactivity
- Automatic cleanup after timeout

---

### 5. FastAPI Application (`main.py`)

**Updated heartbeat configuration:**

```python
HEARTBEAT_INTERVAL_SECONDS = 30  # Send ping every 30 seconds
HEARTBEAT_TIMEOUT_SECONDS = 300  # 5 minutes idle timeout
```

**Heartbeat Mechanism:**
- Server sends `{"type": "ping"}` every 30 seconds
- Closes connection if no activity for 5 minutes
- Client can respond with `{"type": "pong"}`

---

### 6. NGINX Configuration (`nginx.websocket.conf`)

**Updated proxy timeouts:**

```nginx
location /terminal {
    proxy_pass http://powershell-engine:4042;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Long-running session support (120 minutes)
    proxy_connect_timeout 300;
    proxy_read_timeout 7200;
    proxy_send_timeout 7200;
    
    # Disable buffering for WebSocket
    proxy_buffering off;
}
```

**Changes:**
- `proxy_connect_timeout 300`: 5 minutes to establish connection
- `proxy_read_timeout 7200`: 120 minutes read timeout
- `proxy_send_timeout 7200`: 120 minutes send timeout
- `proxy_buffering off`: Disable buffering for real-time WebSocket

---

## Timeout Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                            │
│                         ↕                                    │
│                  (WebSocket)                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    NGINX Proxy                               │
│  • proxy_connect_timeout: 300s (5 min)                      │
│  • proxy_read_timeout: 7200s (120 min)                      │
│  • proxy_send_timeout: 7200s (120 min)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Gunicorn                                  │
│  • timeout: 7200s (120 min)                                 │
│  • keepalive: 300s (5 min)                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                Uvicorn Worker                                │
│  • ws_ping_interval: 30s                                    │
│  • ws_ping_timeout: 300s (5 min)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application                             │
│  • Heartbeat interval: 30s                                  │
│  • Heartbeat timeout: 300s (5 min)                          │
│  • Session TTL: 7200s (120 min)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Connection Lifecycle

1. **Connection Establishment** (0-5 minutes)
   - Client connects to WebSocket endpoint
   - NGINX allows up to 5 minutes for connection setup
   - Session created with 120-minute TTL

2. **Active Session** (0-120 minutes)
   - Server sends ping every 30 seconds
   - Client activity resets session timer
   - All timeouts allow up to 120 minutes

3. **Idle Detection** (5 minutes)
   - If no activity for 5 minutes, WebSocket closes
   - Session data remains for 120 minutes total
   - User can reconnect with same session_id

4. **Session Cleanup** (120 minutes)
   - Background task runs every 5 minutes
   - Removes sessions older than 120 minutes
   - Frees memory and resources

### Heartbeat Flow

```
Server                          Client
  |                               |
  |----{"type": "ping"}---------->|
  |                               |
  |<---{"type": "pong"}-----------|
  |                               |
  |    (30 seconds later)         |
  |                               |
  |----{"type": "ping"}---------->|
  |                               |
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_long_session.py
```

**Tests verify:**
- ✓ Session TTL is 7200 seconds
- ✓ Sessions survive 119 minutes
- ✓ Sessions cleaned after 120 minutes
- ✓ Touch extends session lifetime
- ✓ Multiple sessions handled correctly
- ✓ Heartbeat configuration
- ✓ Gunicorn configuration
- ✓ Uvicorn worker configuration

---

## Environment Variables

Override defaults with environment variables:

```bash
# Gunicorn
GUNICORN_TIMEOUT=7200        # Worker timeout (seconds)
GUNICORN_KEEPALIVE=300       # Keep-alive timeout (seconds)

# Logging
LOG_LEVEL=WARNING            # Log level (DEBUG, INFO, WARNING, ERROR)

# Workers
WEB_CONCURRENCY=4            # Number of worker processes
```

---

## Deployment

### Docker Compose

```yaml
services:
  powershell-engine:
    build: .
    ports:
      - "4042:4042"
    environment:
      - GUNICORN_TIMEOUT=7200
      - GUNICORN_KEEPALIVE=300
      - LOG_LEVEL=WARNING
```

### Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: powershell-config
data:
  GUNICORN_TIMEOUT: "7200"
  GUNICORN_KEEPALIVE: "300"
  LOG_LEVEL: "WARNING"
```

---

## Monitoring

### Key Metrics to Monitor

1. **Active Sessions**
   - Track number of active sessions
   - Alert if approaching memory limits

2. **Session Duration**
   - Monitor average session length
   - Identify long-running sessions

3. **WebSocket Disconnections**
   - Track disconnect rate
   - Investigate if > 1% disconnect unexpectedly

4. **Heartbeat Failures**
   - Monitor ping/pong success rate
   - Alert on connection issues

### Logging

Enable debug logging for troubleshooting:

```bash
LOG_LEVEL=DEBUG python main.py
```

---

## Troubleshooting

### Issue: WebSocket disconnects before 120 minutes

**Check:**
1. NGINX timeout configuration
2. Load balancer timeouts (if applicable)
3. Client-side timeout settings
4. Network infrastructure timeouts

**Solution:**
Ensure all layers support 120-minute timeouts.

### Issue: High memory usage

**Check:**
1. Number of active sessions
2. Session cleanup running properly
3. Memory leaks in session data

**Solution:**
- Reduce SESSION_TTL_SECONDS if needed
- Increase cleanup frequency
- Monitor session data size

### Issue: Frequent heartbeat timeouts

**Check:**
1. Network stability
2. Client responsiveness
3. Server load

**Solution:**
- Increase HEARTBEAT_TIMEOUT_SECONDS
- Reduce HEARTBEAT_INTERVAL_SECONDS
- Scale horizontally

---

## Performance Considerations

### Memory Usage

- Each session: ~10-50 KB
- 1000 concurrent sessions: ~10-50 MB
- Monitor and scale accordingly

### CPU Usage

- Heartbeat overhead: Minimal (<1% per 1000 sessions)
- Command execution: Variable based on workload

### Network Bandwidth

- Heartbeat: ~100 bytes every 30 seconds
- 1000 sessions: ~3.3 KB/s (~26 Kbps)

---

## Best Practices

1. **Client Implementation**
   - Respond to server pings with pongs
   - Implement reconnection logic
   - Store session_id for reconnection

2. **Load Balancing**
   - Use sticky sessions (session affinity)
   - Configure load balancer timeouts
   - Health check endpoints

3. **Monitoring**
   - Track session metrics
   - Alert on anomalies
   - Log important events

4. **Scaling**
   - Horizontal scaling for more sessions
   - Shared session storage (Redis) for multi-instance
   - Connection pooling

---

## Summary

✅ **Achieved:**
- 120-minute session support
- Stable WebSocket connections
- Automatic cleanup
- Heartbeat mechanism
- Production-ready configuration

✅ **Benefits:**
- No premature disconnections
- Better user experience
- Reliable long-running tests
- Efficient resource management

✅ **Tested:**
- All timeout configurations verified
- Session lifecycle validated
- Cleanup mechanism confirmed
- Backward compatibility maintained
