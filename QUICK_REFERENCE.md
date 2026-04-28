# PowerShell Engine - Quick Reference Card

## 🆕 New Commands (Quick Syntax)

```powershell
# Data Processing
Measure-Object                              # Count lines from pipe
Sort-Object                                 # Sort alphabetically
Sort-Object Id                              # Sort by property
Select-Object Id                            # Extract column
Select-Object -First N                      # Limit output

# System Info
Get-Date                                    # Current timestamp
Get-Location                                # Current directory
Get-ChildItem Env:                          # List env vars
set                                         # List env vars (CMD style)

# File Operations
Rename-Item old.txt new.txt                 # Rename file
Copy-Item source.txt dest.txt               # Copy file
Move-Item source.txt dest.txt               # Move file
```

---

## 🔗 Pipeline Examples

```powershell
# Count lines
Get-Content file.txt | Measure-Object

# Sort and count
Get-Content file.txt | Sort-Object | Measure-Object

# Filter, sort, limit
Get-Content log.txt | Select-String ERROR | Sort-Object | Select-Object -First 5

# Process analysis
Get-Process | Sort-Object Id | Select-Object Id

# Complete workflow
Get-Content data.txt | Select-String pattern | Sort-Object | Select-Object -First 10 | Measure-Object
```

---

## 📋 Common Workflows

### Log Analysis
```powershell
Get-Content app.log | Select-String ERROR | Measure-Object
```

### User Management
```powershell
Get-Content users.txt | Sort-Object | Select-Object -First 5
```

### File Organization
```powershell
Rename-Item old.txt new.txt
Copy-Item new.txt backup.txt
```

### Environment Check
```powershell
$env:APP_NAME="MyApp"
Get-ChildItem Env:
```

### System Info
```powershell
Get-Date
Get-Location
pwd
```

---

## ⚡ All Commands (Alphabetical)

```
Add-Content          - Append to file
cd                   - Change directory
cls                  - Clear screen
Copy-Item / copy     - Copy file
dir / ls             - List directory
Get-ChildItem Env:   - List environment
Get-Content / type   - Read file
Get-Date             - Current timestamp
Get-Location         - Current directory
Get-Process          - List processes
Measure-Object       - Count lines
Move-Item / move     - Move file
New-Item / mkdir     - Create file/dir
pwd                  - Print working dir
Remove-Item          - Delete file/dir
Rename-Item          - Rename file
Select-Object        - Extract/limit data
Select-String        - Filter lines
Set-Content          - Write file
set                  - List environment
Sort-Object          - Sort data
Stop-Process         - Kill process
Write-Output / echo  - Print text
$env:KEY=value       - Set env var
>                    - Redirect output
|                    - Pipeline
```

---

## 🎯 Top 10 Most Useful Pipelines

1. `Get-Content file.txt | Measure-Object`
2. `Get-Content file.txt | Sort-Object`
3. `Get-Content file.txt | Select-Object -First 10`
4. `Get-Content log.txt | Select-String ERROR`
5. `Get-Content log.txt | Select-String ERROR | Measure-Object`
6. `Get-Process | Sort-Object Id`
7. `Get-Process | Select-Object Id`
8. `Get-Content data.txt | Sort-Object | Select-Object -First 5`
9. `Get-Content file.txt | Select-String pattern | Measure-Object`
10. `Get-Process | Sort-Object Id | Select-Object Id | Measure-Object`

---

## 🚨 Common Errors

```
Invalid command              - Command not recognized
file not found              - File doesn't exist
invalid arguments           - Wrong syntax
Path does not exist         - Directory not found
Item not found              - Generic missing item
Access denied               - Permission error
Cannot remove directory     - Need -Recurse flag
```

---

## 💡 Pro Tips

1. **Chain pipelines** for powerful data processing
2. **Use Sort-Object** before Select-Object -First
3. **Measure-Object** works on any piped text
4. **Get-Date** for timestamps in logs
5. **Get-ChildItem Env:** to debug environment
6. **Rename-Item** preserves file content
7. **Copy-Item** before risky operations
8. **Select-String** + **Measure-Object** = quick counts
9. **Sort-Object Id** for process analysis
10. **Get-Location** to verify current path

---

## 🎓 Learning Path

### Beginner
```powershell
Get-Date
Get-Location
dir
Get-Content file.txt
```

### Intermediate
```powershell
Get-Content file.txt | Sort-Object
Get-Content file.txt | Measure-Object
Rename-Item old.txt new.txt
```

### Advanced
```powershell
Get-Content log.txt | Select-String ERROR | Measure-Object
Get-Process | Sort-Object Id | Select-Object Id
Get-Content data.txt | Sort-Object | Select-Object -First 10 | Measure-Object
```

---

## 📞 Quick Help

- **Syntax**: `Command-Verb [-Parameter] [value]`
- **Pipeline**: `Command1 | Command2 | Command3`
- **Environment**: `$env:NAME="value"`
- **Redirection**: `Command > output.txt`
- **Quotes**: Use `"text"` or `'text'` for strings with spaces

---

## ✅ Testing Checklist

- [ ] All 10 new commands work
- [ ] Multi-stage pipelines execute
- [ ] Error messages are clear
- [ ] File operations preserve content
- [ ] Environment variables persist
- [ ] Session state maintained
- [ ] WebSocket connection stable

---

**Version**: 2.0 (Enterprise Edition)
**Commands**: 30+
**Pipeline Stages**: Unlimited
**Status**: Production Ready ✅
