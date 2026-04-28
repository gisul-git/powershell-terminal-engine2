# PowerShell Engine - Command Quick Reference

## 🚀 Quick Command Lookup

### File System Commands
```powershell
Get-ChildItem              # List files and folders
dir                        # List directory (traditional)
ls                         # List directory (Unix-style)
Get-Item file.txt          # Get file/folder details
Test-Path file.txt         # Check if path exists (True/False)
New-Item file.txt -ItemType File
Remove-Item file.txt
Get-Content file.txt
Set-Content file.txt "text"
Add-Content file.txt "text"
Rename-Item old.txt new.txt
Copy-Item source.txt dest.txt
Move-Item source.txt dest.txt
```

### Service Management
```powershell
Get-Service                # List all services
Start-Service WSearch      # Start a service
Stop-Service Spooler       # Stop a service
Restart-Service WinDefend  # Restart a service
```

### Network Commands
```powershell
ipconfig                   # Network configuration
Test-Connection google.com # Ping simulation
Resolve-DnsName google.com # DNS lookup
```

### System Information
```powershell
whoami                     # Current user
hostname                   # Computer name
Get-ComputerInfo           # System details
Get-Location               # Current directory
Get-Date                   # Current date/time
```

### Archive Operations
```powershell
Compress-Archive file.txt backup.zip
Expand-Archive backup.zip restored.txt
```

### Process Management
```powershell
Get-Process                # List processes
Stop-Process -Id 102       # Kill process
```

### Pipeline Commands
```powershell
Measure-Object             # Count lines
Sort-Object                # Sort alphabetically
Sort-Object Id             # Sort by property
Select-Object Id           # Extract column
Select-Object -First 5     # Limit output
Where-Object Id -gt 101    # Filter by property
ForEach-Object             # Process each item
Select-String ERROR        # Filter lines
```

### Environment
```powershell
$env:KEY="value"           # Set environment variable
Get-ChildItem Env:         # List environment variables
set                        # List environment (CMD-style)
```

### Utilities
```powershell
cd path                    # Change directory
pwd                        # Print working directory
cls                        # Clear screen
echo "text"                # Print text
command > file.txt         # Redirect output
```

---

## 🔗 Common Pipeline Patterns

### Log Analysis
```powershell
Get-Content app.log | Select-String ERROR
Get-Content app.log | Select-String ERROR | Measure-Object
```

### Process Filtering
```powershell
Get-Process | Where-Object Id -gt 101
Get-Process | Sort-Object Id | Select-Object Id
```

### File Operations
```powershell
Get-ChildItem | Where-Object Name -eq app.log
Get-ChildItem | Sort-Object | Select-Object -First 5
```

### Data Processing
```powershell
Get-Content data.txt | Sort-Object | Select-Object -First 10
Get-Content data.txt | Select-String pattern | Measure-Object
```

---

## 🎯 Top 20 Most Useful Commands

1. `Get-ChildItem` / `dir` / `ls` - List files
2. `Get-Service` - View services
3. `Start-Service` - Start service
4. `Test-Path` - Check existence
5. `Get-Item` - File details
6. `ipconfig` - Network info
7. `Test-Connection` - Ping
8. `whoami` - Current user
9. `hostname` - Computer name
10. `Get-ComputerInfo` - System info
11. `Compress-Archive` - Create backup
12. `Expand-Archive` - Restore backup
13. `Where-Object` - Filter data
14. `Get-Content` - Read file
15. `Select-String` - Find pattern
16. `Measure-Object` - Count lines
17. `Sort-Object` - Sort data
18. `Get-Process` - List processes
19. `Restart-Service` - Restart service
20. `Resolve-DnsName` - DNS lookup

---

## 📋 Command Categories

**File System (11)**: Get-ChildItem, dir, ls, Get-Item, Test-Path, New-Item, Remove-Item, Get-Content, Set-Content, Rename-Item, Copy-Item, Move-Item

**Services (4)**: Get-Service, Start-Service, Stop-Service, Restart-Service

**Network (3)**: ipconfig, Test-Connection, Resolve-DnsName

**System (6)**: whoami, hostname, Get-ComputerInfo, Get-Location, Get-Date, pwd

**Archive (2)**: Compress-Archive, Expand-Archive

**Process (2)**: Get-Process, Stop-Process

**Pipeline (7)**: Measure-Object, Sort-Object, Select-Object, Where-Object, ForEach-Object, Select-String

**Environment (3)**: $env:KEY=value, Get-ChildItem Env:, set

**Utilities (4)**: cd, cls, echo, >

---

## ⚡ Keyboard Shortcuts

- `cls` - Clear screen
- `cd ..` - Go up one directory
- `cd ~` - Go to home directory
- `pwd` - Show current path

---

## 🎓 Learning Path

### Level 1: Basics
```powershell
dir
cd folder
pwd
Get-Content file.txt
whoami
hostname
```

### Level 2: Intermediate
```powershell
Get-Service
Start-Service WSearch
ipconfig
Test-Path file.txt
Get-Item file.txt
Compress-Archive file.txt backup.zip
```

### Level 3: Advanced
```powershell
Get-Process | Where-Object Id -gt 101
Get-Content log.txt | Select-String ERROR | Measure-Object
Get-ChildItem | Where-Object Name -eq app.log
Get-Service | Where-Object Status -eq Running
```

---

## 🚨 Common Errors

- `Invalid command` - Command not recognized
- `file not found` - File doesn't exist
- `invalid arguments` - Wrong syntax
- `service not found` - Invalid service name
- `Path does not exist` - Directory not found

---

## 💡 Pro Tips

1. Use `Test-Path` before file operations
2. Chain `Where-Object` with other pipeline commands
3. Use `Measure-Object` to count filtered results
4. `Get-Service` shows real-time service status
5. `Compress-Archive` preserves file content
6. `ipconfig` shows simulated network info
7. `Get-Item` provides file size information
8. Combine `Sort-Object` with `Select-Object -First`

---

## 📊 Command Syntax Patterns

**No Arguments:**
```powershell
Get-Service
Get-Process
ipconfig
whoami
hostname
Get-ComputerInfo
```

**Single Argument:**
```powershell
Get-Item file.txt
Test-Path file.txt
Start-Service WSearch
Test-Connection google.com
```

**Two Arguments:**
```powershell
Rename-Item old.txt new.txt
Copy-Item source.txt dest.txt
Compress-Archive file.txt backup.zip
```

**With Flags:**
```powershell
New-Item file.txt -ItemType File
Select-Object -First 5
Remove-Item folder -Recurse
```

**Pipeline:**
```powershell
Command1 | Command2
Command1 | Command2 | Command3
```

---

## 🎯 Scenario-Based Commands

### Troubleshooting Network
```powershell
ipconfig
Test-Connection google.com
Resolve-DnsName google.com
hostname
```

### Managing Services
```powershell
Get-Service
Start-Service WSearch
Restart-Service WinDefend
Get-Service
```

### File Backup
```powershell
Test-Path important.txt
Compress-Archive important.txt backup.zip
Test-Path backup.zip
```

### Log Analysis
```powershell
Get-Content app.log | Select-String ERROR
Get-Content app.log | Select-String ERROR | Measure-Object
```

### System Audit
```powershell
whoami
hostname
Get-ComputerInfo
Get-Service
Get-Process
```

---

**Total Commands**: 50+
**Categories**: 9
**Aliases**: 10+
**Pipeline Stages**: Unlimited

**Version**: 3.0 Enterprise Edition ✅
