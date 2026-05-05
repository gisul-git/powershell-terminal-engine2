# Deployment Checklist - Long Session Support

## Pre-Deployment Verification

### ✅ Code Changes
- [x] Dockerfile updated with `--timeout 7200 --keep-alive 300`
- [x] gunicorn_conf.py timeout set to 7200s
- [x] gunicorn_conf.py keepalive set to 300s
- [x] gunicorn_worker.py ws_ping_interval set to 30s
- [x] gunicorn_worker.py ws_ping_timeout set to 300s
- [x] session_manager.py SESSION_TTL_SECONDS set to 7200s
- [x] main.py HEARTBEAT_INTERVAL_SECONDS set to 30s
- [x] main.py HEARTBEAT_TIMEOUT_SECONDS set to 300s
- [x] nginx.websocket.conf proxy_read_timeout set to 7200s
- [x] nginx.websocket.conf proxy_send_timeout set to 7200s
- [x] nginx.websocket.conf proxy_connect_timeout set to 300s
- [x] nginx.websocket.conf proxy_buffering set to off

### ✅ Testing
- [x] All 8 configuration tests pass
- [x] Session TTL verified (7200s)
- [x] Session survives 119 minutes
- [x] Session cleaned after 120 minutes
- [x] Touch extends session lifetime
- [x] Multiple sessions handled correctly
- [x] Heartbeat configuration verified
- [x] Gunicorn configuration verified
- [x] Uvicorn worker configuration verified

### ✅ Documentation
- [x] LONG_SESSION_CONFIGURATION.md created
- [x] TIMEOUT_QUICK_REFERENCE.md created
- [x] UPGRADE_SUMMARY_LONG_SESSIONS.md created
- [x] ARCHITECTURE_DIAGRAM.md created
- [x] DEPLOYMENT_CHECKLIST.md created

---

## Deployment Steps

### Step 1: Backup Current Configuration
```bash
# Backup current files
cp Dockerfile Dockerfile.backup
cp gunicorn_conf.py gunicorn_conf.py.backup
cp gunicorn_worker.py gunicorn_worker.py.backup
cp session_manager.py session_manager.py.backup
cp main.py main.py.backup
cp nginx.websocket.conf nginx.websocket.conf.backup
```
- [ ] Backups created

### Step 2: Build Docker Image
```bash
# Build new image
docker build -t powershell-engine:long-session .

# Verify build
docker images | grep powershell-engine
```
- [ ] Docker image built successfully
- [ ] Image tagged as `powershell-engine:long-session`

### Step 3: Test Locally (Optional but Recommended)
```bash
# Run container locally
docker run -d \
  --name powershell-test \
  -p 4043:4042 \
  -e LOG_LEVEL=DEBUG \
  powershell-engine:long-session

# Check logs
docker logs powershell-test

# Test WebSocket connection
# (Use your WebSocket client to connect to ws://localhost:4043/terminal)

# Stop test container
docker stop powershell-test
docker rm powershell-test
```
- [ ] Local test successful
- [ ] WebSocket connection works
- [ ] Commands execute properly
- [ ] Heartbeat visible in logs

### Step 4: Update NGINX Configuration
```bash
# Backup current NGINX config
sudo cp /etc/nginx/conf.d/powershell.conf /etc/nginx/conf.d/powershell.conf.backup

# Copy new configuration
sudo cp nginx.websocket.conf /etc/nginx/conf.d/powershell.conf

# Test NGINX configuration
sudo nginx -t
```
- [ ] NGINX config backed up
- [ ] New config copied
- [ ] NGINX test passed

### Step 5: Reload NGINX
```bash
# Reload NGINX (no downtime)
sudo nginx -s reload

# Or restart if needed
# sudo systemctl restart nginx

# Verify NGINX is running
sudo systemctl status nginx
```
- [ ] NGINX reloaded successfully
- [ ] NGINX status is active

### Step 6: Deploy Container
```bash
# Stop old container
docker stop powershell-engine

# Remove old container
docker rm powershell-engine

# Start new container
docker run -d \
  --name powershell-engine \
  --restart unless-stopped \
  -p 4042:4042 \
  -e LOG_LEVEL=WARNING \
  -e GUNICORN_TIMEOUT=7200 \
  -e GUNICORN_KEEPALIVE=300 \
  powershell-engine:long-session

# Verify container is running
docker ps | grep powershell-engine
```
- [ ] Old container stopped
- [ ] Old container removed
- [ ] New container started
- [ ] Container is running

### Step 7: Verify Deployment
```bash
# Check container logs
docker logs powershell-engine --tail 50

# Check for errors
docker logs powershell-engine | grep ERROR

# Verify configuration
docker exec powershell-engine python -c "
from session_manager import SESSION_TTL_SECONDS
from main import HEARTBEAT_INTERVAL_SECONDS, HEARTBEAT_TIMEOUT_SECONDS
import gunicorn_conf
print(f'Session TTL: {SESSION_TTL_SECONDS}s')
print(f'Heartbeat: {HEARTBEAT_INTERVAL_SECONDS}s / {HEARTBEAT_TIMEOUT_SECONDS}s')
print(f'Gunicorn: {gunicorn_conf.timeout}s / {gunicorn_conf.keepalive}s')
"
```
- [ ] No errors in logs
- [ ] Configuration values correct
- [ ] Container healthy

### Step 8: Test WebSocket Connection
```bash
# Test WebSocket endpoint
# Use your WebSocket client or browser console:

# JavaScript example:
# const ws = new WebSocket('wss://your-domain.com/terminal');
# ws.onopen = () => console.log('Connected');
# ws.onmessage = (e) => console.log('Message:', e.data);
# ws.send(JSON.stringify({type: 'command', data: 'Get-Location'}));
```
- [ ] WebSocket connection established
- [ ] Init message received
- [ ] Commands execute successfully
- [ ] Ping messages received every 30s

### Step 9: Monitor for 10 Minutes
```bash
# Watch logs in real-time
docker logs -f powershell-engine

# In another terminal, monitor connections
watch -n 5 'netstat -an | grep 4042 | grep ESTABLISHED | wc -l'

# Monitor memory usage
watch -n 5 'docker stats powershell-engine --no-stream'
```
- [ ] No errors in logs
- [ ] Connections stable
- [ ] Memory usage normal
- [ ] Heartbeat working

### Step 10: Long-Running Test (Optional)
```bash
# Create a test session and leave it idle for 30+ minutes
# Verify:
# 1. Connection stays alive
# 2. Heartbeat continues
# 3. Session persists
# 4. Can execute commands after idle period
```
- [ ] Session survives 30+ minutes
- [ ] Heartbeat continues
- [ ] Commands work after idle

---

## Post-Deployment Verification

### Immediate Checks (0-5 minutes)
- [ ] Container is running
- [ ] No errors in logs
- [ ] WebSocket connections work
- [ ] Commands execute properly
- [ ] Heartbeat visible

### Short-term Checks (5-30 minutes)
- [ ] Connections remain stable
- [ ] No memory leaks
- [ ] No CPU spikes
- [ ] Heartbeat continues
- [ ] Sessions persist

### Long-term Checks (30-120 minutes)
- [ ] Sessions survive 60+ minutes
- [ ] Sessions survive 90+ minutes
- [ ] Sessions survive 119 minutes
- [ ] Sessions cleaned after 120 minutes
- [ ] No resource exhaustion

---

## Rollback Plan

If issues occur, rollback immediately:

### Quick Rollback
```bash
# Stop new container
docker stop powershell-engine
docker rm powershell-engine

# Restore old container
docker run -d \
  --name powershell-engine \
  --restart unless-stopped \
  -p 4042:4042 \
  -e LOG_LEVEL=WARNING \
  powershell-engine:previous-version

# Restore NGINX config
sudo cp /etc/nginx/conf.d/powershell.conf.backup /etc/nginx/conf.d/powershell.conf
sudo nginx -s reload
```

### Full Rollback
```bash
# Restore all files
cp Dockerfile.backup Dockerfile
cp gunicorn_conf.py.backup gunicorn_conf.py
cp gunicorn_worker.py.backup gunicorn_worker.py
cp session_manager.py.backup session_manager.py
cp main.py.backup main.py
cp nginx.websocket.conf.backup nginx.websocket.conf

# Rebuild and deploy
docker build -t powershell-engine:rollback .
docker stop powershell-engine
docker rm powershell-engine
docker run -d --name powershell-engine -p 4042:4042 powershell-engine:rollback

# Restore NGINX
sudo cp /etc/nginx/conf.d/powershell.conf.backup /etc/nginx/conf.d/powershell.conf
sudo nginx -s reload
```

---

## Monitoring Checklist

### Metrics to Monitor
- [ ] Active WebSocket connections
- [ ] Session count
- [ ] Memory usage
- [ ] CPU usage
- [ ] Error rate
- [ ] Average session duration
- [ ] Heartbeat success rate

### Alerts to Configure
- [ ] Container down
- [ ] High error rate (>1%)
- [ ] High memory usage (>80%)
- [ ] High CPU usage (>80%)
- [ ] Session count spike
- [ ] Heartbeat failures

### Logs to Review
- [ ] Application logs (docker logs)
- [ ] NGINX access logs
- [ ] NGINX error logs
- [ ] System logs

---

## Success Criteria

### Deployment is successful if:
- ✅ All tests pass (8/8)
- ✅ Container runs without errors
- ✅ WebSocket connections stable
- ✅ Commands execute properly
- ✅ Heartbeat working (30s interval)
- ✅ Sessions survive 60+ minutes
- ✅ Sessions cleaned after 120 minutes
- ✅ No memory leaks
- ✅ No performance degradation
- ✅ User experience improved

### Deployment should be rolled back if:
- ❌ Tests fail
- ❌ Container crashes
- ❌ WebSocket disconnects frequently
- ❌ Commands fail to execute
- ❌ Memory usage spikes
- ❌ Performance degrades
- ❌ User experience worsens

---

## Contact Information

### Support Channels
- Technical Lead: [Name/Email]
- DevOps Team: [Email/Slack]
- On-Call: [Phone/Pager]

### Documentation
- Full Guide: LONG_SESSION_CONFIGURATION.md
- Quick Reference: TIMEOUT_QUICK_REFERENCE.md
- Architecture: ARCHITECTURE_DIAGRAM.md
- Summary: UPGRADE_SUMMARY_LONG_SESSIONS.md

---

## Sign-Off

### Pre-Deployment
- [ ] Code reviewed by: _________________ Date: _______
- [ ] Tests verified by: _________________ Date: _______
- [ ] Approved by: ______________________ Date: _______

### Post-Deployment
- [ ] Deployed by: ______________________ Date: _______
- [ ] Verified by: ______________________ Date: _______
- [ ] Signed off by: ____________________ Date: _______

---

**Deployment Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Rolled Back

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________
