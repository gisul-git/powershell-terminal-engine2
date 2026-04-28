# Advanced Windows Administration Commands - Reference

## 🎯 Overview

This document covers the advanced Windows administration commands added to the PowerShell Engine, making it enterprise-grade and suitable for professional assessments and CEO demonstrations.

---

## 📋 New Commands Summary

| Command | Category | Description |
|---------|----------|-------------|
| Get-ChildItem | File System | Enhanced directory listing |
| dir | File System | Alias for directory listing |
| ls | File System | Unix-style directory listing |
| Get-Item | File System | Get file/folder details |
| Test-Path | File System | Check if path exists |
| Get-Service | Services | List Windows services |
| Start-Service | Services | Start a service |
| Stop-Service | Services | Stop a service |
| Restart-Service | Services | Restart a service |
| Test-Connection | Network | Ping simulation |
| ipconfig | Network | Network configuration |
| Resolve-DnsName | Network | DNS lookup |
| whoami | System | Current user |
| hostname | System | Computer name |
| Get-ComputerInfo | System | System information |
| Compress-Archive | Archive | Create zip file |
| Expand-Archive | Archive | Extract zip file |
| Where-Object | Pipeline | Filter objects |
| ForEach-Object | Pipeline | Process each item |

---

## 📁 File System Commands

### Get-ChildItem / dir / ls

Enhanced directory listing with clean output.

**Syntax:**
```powershell
Get-ChildItem
dir
ls
```

**Output:**
```
Mode   Name
----   ----
Dir    logs
File   app.log
File   data.txt
```

**Notes:**
- `dir` shows traditional PowerShell format
- `ls` and `Get-ChildItem` show simplified format
- All three commands work identically

---

### Get-Item

Returns detailed information about a file or folder.

**Syntax:**
```powershell
Get-Item filename.txt
Get-Item foldername
```

**Output (File):**
```
Name : app.log
Type : File
Size : 124
```

**Output (Directory):**
```
Name : logs
Type : Directory
```

---

### Test-Path

Checks if a path exists.

**Syntax:**
```powershell
Test-Path filename.txt
Test-Path C:\path\to\file
```

**Output:**
```
True    # If exists
False   # If not found
```

**Use Cases:**
- Validate file existence before operations
- Check directory availability
- Conditional script logic

---

## 🔧 Service Management Commands

### Get-Service

Lists all Windows services with their status.

**Syntax:**
```powershell
Get-Service
```

**Output:**
```
Status   Name
------   ----
Running  Spooler
Running  WinDefend
Stopped  WSearch
```

**Default Services:**
- Spooler (Print Spooler) - Running
- WinDefend (Windows Defender) - Running
- WSearch (Windows Search) - Stopped

---

### Start-Service

Starts a stopped Windows service.

**Syntax:**
```powershell
Start-Service ServiceName
```

**Example:**
```powershell
Start-Service WSearch
Get-Service  # Verify it's running
```

**Errors:**
- `Service not found` - Invalid service name

---

### Stop-Service

Stops a running Windows service.

**Syntax:**
```powershell
Stop-Service ServiceName
```

**Example:**
```powershell
Stop-Service Spooler
Get-Service  # Verify it's stopped
```

---

### Restart-Service

Restarts a Windows service (stops then starts).

**Syntax:**
```powershell
Restart-Service ServiceName
```

**Example:**
```powershell
Restart-Service WinDefend
Get-Service  # Verify it's running
```

**Behavior:**
- Always results in "Running" status
- Simulates stop → start sequence

---

## 🌐 Network Commands

### Test-Connection

Simulated ping command to test network connectivity.

**Syntax:**
```powershell
Test-Connection hostname
Test-Connection google.com
```

**Output:**
```
Reply from google.com
Reply from google.com
Packets: Sent = 2, Received = 2
```

**Notes:**
- Always succeeds (simulated)
- Returns 2 successful replies
- Useful for network troubleshooting demos

---

### ipconfig

Displays network configuration information.

**Syntax:**
```powershell
ipconfig
```

**Output:**
```
IPv4 Address . . . . . : 192.168.1.10
Subnet Mask . . . . . : 255.255.255.0
Gateway . . . . . . . : 192.168.1.1
```

**Simulated Values:**
- IP: 192.168.1.10
- Subnet: 255.255.255.0
- Gateway: 192.168.1.1

---

### Resolve-DnsName

Performs DNS name resolution.

**Syntax:**
```powershell
Resolve-DnsName hostname
Resolve-DnsName google.com
```

**Output:**
```
Name : google.com
Address : 142.250.0.1
```

**Notes:**
- Returns simulated IP address
- Useful for DNS troubleshooting scenarios

---

## 💻 System Information Commands

### whoami

Returns the current user name.

**Syntax:**
```powershell
whoami
```

**Output:**
```
User
```

**Use Cases:**
- Verify current user context
- Security auditing
- Script validation

---

### hostname

Returns the computer name.

**Syntax:**
```powershell
hostname
```

**Output:**
```
WIN-SERVER01
```

**Use Cases:**
- Identify current machine
- Remote management scenarios
- Inventory scripts

---

### Get-ComputerInfo

Returns detailed system information.

**Syntax:**
```powershell
Get-ComputerInfo
```

**Output:**
```
OSName : Windows Server
OSVersion : 2022
ComputerName : WIN-SERVER01
```

**Information Provided:**
- Operating System Name
- OS Version
- Computer Name

---

## 📦 Archive Commands

### Compress-Archive

Creates a compressed archive (zip file).

**Syntax:**
```powershell
Compress-Archive source.txt destination.zip
```

**Example:**
```powershell
New-Item data.txt -ItemType File
Set-Content data.txt "Important data"
Compress-Archive data.txt backup.zip
```

**Behavior:**
- Creates zip file in virtual filesystem
- Preserves original file content
- Stores content in metadata for extraction

---

### Expand-Archive

Extracts files from a compressed archive.

**Syntax:**
```powershell
Expand-Archive source.zip destination.txt
```

**Example:**
```powershell
Expand-Archive backup.zip restored.txt
Get-Content restored.txt  # View extracted content
```

**Behavior:**
- Extracts content from zip file
- Creates new file with original content
- Validates archive format

---

## 🔄 Pipeline Commands

### Where-Object

Filters objects based on property values.

**Syntax:**
```powershell
Command | Where-Object Property Operator Value
```

**Operators:**
- `-gt` - Greater than
- `-lt` - Less than
- `-eq` - Equal to

**Examples:**

**Filter processes by ID:**
```powershell
Get-Process | Where-Object Id -gt 101
```

**Filter files by name:**
```powershell
Get-ChildItem | Where-Object Name -eq app.log
```

**Complex pipeline:**
```powershell
Get-Process | Where-Object Id -gt 100 | Sort-Object Id
```

---

### ForEach-Object

Processes each item in a pipeline.

**Syntax:**
```powershell
Command | ForEach-Object
```

**Example:**
```powershell
Get-Content users.txt | ForEach-Object
```

**Behavior:**
- Simple pass-through implementation
- Returns all items unchanged
- Useful for pipeline demonstrations

---

## 🔗 Advanced Pipeline Examples

### Example 1: Service Management
```powershell
Get-Service
Start-Service WSearch
Get-Service | Where-Object Status -eq Running
```

### Example 2: File Analysis
```powershell
Get-ChildItem
Get-ChildItem | Where-Object Name -eq app.log
Get-Item app.log
```

### Example 3: Network Diagnostics
```powershell
ipconfig
Test-Connection google.com
Resolve-DnsName google.com
hostname
```

### Example 4: System Audit
```powershell
whoami
hostname
Get-ComputerInfo
Get-Service
Get-Process | Sort-Object Id
```

### Example 5: Archive Operations
```powershell
New-Item important.txt -ItemType File
Set-Content important.txt "Critical data"
Compress-Archive important.txt backup.zip
Test-Path backup.zip
Expand-Archive backup.zip restored.txt
Get-Content restored.txt
```

### Example 6: Complex Filtering
```powershell
Get-Process | Where-Object Id -gt 101 | Sort-Object Id | Select-Object Id
```

---

## ⚠️ Error Messages

| Error | Meaning |
|-------|---------|
| Invalid command | Command not recognized |
| file not found | File doesn't exist |
| invalid arguments | Wrong syntax or parameters |
| service not found | Service name not recognized |
| Path does not exist | Directory not found |
| Item not found | Generic item missing |

---

## 🎓 Training Scenarios

### Scenario 1: Windows Administrator Day 1
```powershell
# Check system info
whoami
hostname
Get-ComputerInfo

# View services
Get-Service

# Check network
ipconfig
Test-Connection google.com
```

### Scenario 2: Service Troubleshooting
```powershell
# Check service status
Get-Service

# Restart problematic service
Restart-Service WinDefend

# Verify it's running
Get-Service | Where-Object Name -eq WinDefend
```

### Scenario 3: File Management
```powershell
# List files
Get-ChildItem

# Check if file exists
Test-Path app.log

# Get file details
Get-Item app.log

# Create backup
Compress-Archive app.log backup.zip
```

### Scenario 4: Network Diagnostics
```powershell
# Check IP configuration
ipconfig

# Test connectivity
Test-Connection google.com

# Resolve DNS
Resolve-DnsName google.com

# Identify machine
hostname
```

---

## 🚀 Enterprise Use Cases

1. **IT Assessment Tests** - Realistic Windows admin scenarios
2. **Training Platforms** - Hands-on PowerShell practice
3. **Interview Evaluations** - Technical skill validation
4. **CEO Demonstrations** - Professional terminal showcase
5. **Educational Labs** - Safe Windows environment simulation

---

## 📊 Command Coverage

**Total Commands: 50+**

- File Operations: 15
- Directory Management: 5
- Process Management: 3
- Service Management: 4
- Network Tools: 3
- System Information: 3
- Archive Operations: 2
- Data Processing: 7
- Pipeline Tools: 2
- Utilities: 6+

---

## ✨ Key Features

✅ Enterprise-grade command set
✅ Realistic Windows service management
✅ Network diagnostic tools
✅ Archive operations
✅ Advanced pipeline filtering
✅ System information gathering
✅ Professional output formatting
✅ Consistent error handling
✅ Session-based isolation
✅ WebSocket real-time communication

---

**Version**: 3.0 (Enterprise Edition)
**Status**: Production Ready ✅
**Suitable For**: Professional assessments, CEO demos, training platforms
