# Integration Test Guide

## Testing via WebSocket Terminal

Once the FastAPI server is running, you can test all new commands through the WebSocket terminal interface.

### Starting the Server

```bash
python main.py
# or
uvicorn main:app --reload
```

Then connect to: `ws://localhost:8000/terminal`

---

## Test Commands to Run

### 1. Basic New Commands

```powershell
# Test Get-Date
Get-Date

# Test Get-Location
Get-Location

# Test environment variables
$env:TEST="Hello"
$env:PATH="C:\Windows"
Get-ChildItem Env:
set
```

### 2. File Operations

```powershell
# Create and rename
New-Item test.txt -ItemType File
Add-Content test.txt "content"
Rename-Item test.txt renamed.txt
dir

# Copy and move
Copy-Item renamed.txt copy.txt
Move-Item copy.txt moved.txt
dir
```

### 3. Data Processing Pipelines

```powershell
# Create test data
New-Item users.txt -ItemType File
Add-Content users.txt "charlie"
Add-Content users.txt "alice"
Add-Content users.txt "bob"

# Test Sort-Object
Get-Content users.txt | Sort-Object

# Test Measure-Object
Get-Content users.txt | Measure-Object

# Test Select-Object
Get-Content users.txt | Sort-Object | Select-Object -First 2

# Complex pipeline
Get-Content users.txt | Sort-Object | Select-Object -First 2 | Measure-Object
```

### 4. Log Analysis Scenario

```powershell
# Create log file
New-Item app.log -ItemType File
Add-Content app.log "INFO: Started"
Add-Content app.log "ERROR: Failed"
Add-Content app.log "WARNING: Slow"
Add-Content app.log "ERROR: Timeout"

# Analyze errors
Get-Content app.log | Select-String ERROR
Get-Content app.log | Select-String ERROR | Measure-Object
```

### 5. Process Management

```powershell
# List processes
Get-Process

# Sort by ID
Get-Process | Sort-Object Id

# Extract IDs only
Get-Process | Select-Object Id

# Combined pipeline
Get-Process | Sort-Object Id | Select-Object Id | Measure-Object
```

---

## Expected Behaviors

### ✅ All Commands Should:
- Execute without errors
- Return properly formatted output
- Support piping where applicable
- Handle edge cases gracefully
- Show consistent error messages

### ✅ Pipelines Should:
- Pass output between stages
- Execute sequentially
- Stop on critical errors
- Handle empty input

### ✅ Session Should:
- Maintain filesystem state
- Track current directory
- Store environment variables
- Isolate from other connections

---

## Error Testing

```powershell
# Should show "file not found"
Rename-Item nonexistent.txt new.txt

# Should show "invalid arguments"
Rename-Item onefile.txt

# Should show "invalid arguments"
Get-Date extra

# Should show "invalid arguments"
Get-Location extra
```

---

## Performance Check

All commands should respond within 0.1-0.3 seconds (simulated delay).

---

## WebSocket Message Format

### Client → Server (Command):
```json
{
  "type": "command",
  "data": "Get-Content users.txt | Sort-Object"
}
```

### Server → Client (Response):
```json
{
  "type": "response",
  "data": {
    "output": "alice\nbob\ncharlie",
    "prompt": "PS C:\\Users\\User> "
  }
}
```

---

## Success Criteria

✅ All 10 new commands work correctly
✅ Multi-stage pipelines execute properly
✅ Error handling is consistent
✅ Session state is maintained
✅ WebSocket communication is stable
✅ Output formatting matches PowerShell style

---

## Troubleshooting

### If commands don't work:
1. Check server logs for errors
2. Verify WebSocket connection is established
3. Ensure message format is correct
4. Check session initialization

### If pipelines fail:
1. Test each command individually
2. Check for error propagation
3. Verify output passing between stages
4. Review STOP_ERRORS list

### If session state is lost:
1. Check WebSocket connection status
2. Verify session manager is working
3. Review session cleanup logic
4. Test with single connection first

---

## Load Testing

For production use, test with:
- Multiple concurrent WebSocket connections
- Long-running sessions
- Large file operations
- Complex nested pipelines
- Rapid command execution

---

## Next Steps

After successful integration testing:
1. Deploy to staging environment
2. Conduct user acceptance testing
3. Monitor performance metrics
4. Gather feedback from assessments
5. Iterate based on real-world usage

---

## Support

For issues or questions:
- Review `COMMANDS_REFERENCE.md` for command syntax
- Check `UPGRADE_SUMMARY.md` for implementation details
- Run test scripts: `test_new_commands.py`, `test_edge_cases.py`
- Execute demo: `demo_enterprise.py`
