# PowerShell Engine - Commands Reference

## Overview
This FastAPI + WebSocket PowerShell terminal simulator now supports advanced administrative commands with robust pipeline capabilities.

---

## 🆕 New Commands Added

### 1. Measure-Object
Counts lines from piped input.

**Syntax:**
```powershell
Get-Content file.txt | Measure-Object
```

**Output:**
```
Count : 3
```

---

### 2. Sort-Object
Sorts lines alphabetically or by property.

**Syntax:**
```powershell
Get-Content names.txt | Sort-Object
Get-Process | Sort-Object Id
```

**Examples:**
```powershell
# Alphabetical sort
Get-Content users.txt | Sort-Object

# Sort processes by ID
Get-Process | Sort-Object Id
```

---

### 3. Select-Object
Selects specific properties or limits output.

**Syntax:**
```powershell
Get-Process | Select-Object Id
Get-Process | Select-Object ProcessName
Get-Content file.txt | Select-Object -First 2
```

**Examples:**
```powershell
# Get only process IDs
Get-Process | Select-Object Id

# Get first 3 lines
Get-Content log.txt | Select-Object -First 3
```

---

### 4. Get-Date
Returns current server date and time.

**Syntax:**
```powershell
Get-Date
```

**Output:**
```
2026-04-28 14:22:10
```

---

### 5. Get-Location
Returns current working directory path.

**Syntax:**
```powershell
Get-Location
```

**Output:**
```
Path
----
C:\Users\User\incident
```

---

### 6. Rename-Item
Renames a file while preserving content.

**Syntax:**
```powershell
Rename-Item old.txt new.txt
```

**Errors:**
- `file not found` - Source file doesn't exist
- `invalid arguments` - Wrong number of arguments or target exists

---

### 7. Copy-Item
Alias for existing `copy` command.

**Syntax:**
```powershell
Copy-Item source.txt destination.txt
```

---

### 8. Move-Item
Alias for existing `move` command.

**Syntax:**
```powershell
Move-Item source.txt destination.txt
```

---

### 9. Get-ChildItem Env:
Lists all environment variables.

**Syntax:**
```powershell
Get-ChildItem Env:
```

**Output:**
```
Name        Value
----        -----
PATH        C:\Windows
USER        User
```

---

### 10. set
Shows environment variables (same as `Get-ChildItem Env:`).

**Syntax:**
```powershell
set
```

---

## 🔗 Pipeline Support

The engine now supports complex multi-stage pipelines:

### Examples:

**1. Filter and count errors:**
```powershell
Get-Content app.log | Select-String ERROR | Measure-Object
```

**2. Sort and select top items:**
```powershell
Get-Content users.txt | Sort-Object | Select-Object -First 3
```

**3. Process management:**
```powershell
Get-Process | Sort-Object Id | Select-Object Id
```

**4. Complex data processing:**
```powershell
Get-Content data.txt | Select-String "pattern" | Sort-Object | Measure-Object
```

---

## 📋 Complete Command List

### File Operations
- `New-Item` / `mkdir` - Create files/directories
- `Remove-Item` - Delete files/directories
- `Get-Content` / `type` - Read file content
- `Set-Content` - Write file content
- `Add-Content` - Append to file
- `Copy-Item` / `copy` - Copy files
- `Move-Item` / `move` - Move files
- `Rename-Item` - Rename files

### Directory Operations
- `cd` - Change directory
- `pwd` - Print working directory
- `dir` / `ls` - List directory contents
- `Get-Location` - Get current path

### Process Management
- `Get-Process` - List processes
- `Stop-Process` - Kill process by ID

### Data Processing
- `Select-String` - Filter lines by pattern
- `Sort-Object` - Sort lines
- `Select-Object` - Select properties or limit output
- `Measure-Object` - Count lines

### System Information
- `Get-Date` - Current date/time
- `Get-ChildItem Env:` / `set` - List environment variables

### Utilities
- `Write-Output` / `echo` - Print text
- `cls` - Clear screen

### Environment
- `$env:KEY=value` - Set environment variable

---

## 🧪 Test Cases

### Test 1: Sort and Count
```powershell
New-Item users.txt -ItemType File
Add-Content users.txt "charlie"
Add-Content users.txt "alice"
Add-Content users.txt "bob"
Get-Content users.txt | Sort-Object
```
**Expected:**
```
alice
bob
charlie
```

### Test 2: Measure
```powershell
Get-Content users.txt | Measure-Object
```
**Expected:**
```
Count : 3
```

### Test 3: Rename
```powershell
Rename-Item users.txt members.txt
dir
```
**Expected:** Directory listing shows `members.txt`

### Test 4: Complex Pipeline
```powershell
Get-Content app.log | Select-String ERROR | Measure-Object
```
**Expected:** Count of lines containing "ERROR"

---

## ⚠️ Error Messages

Consistent error responses:
- `Invalid command` - Command not recognized
- `file not found` - File doesn't exist
- `invalid arguments` - Wrong arguments provided
- `Path does not exist` - Directory not found
- `Item not found` - Generic item missing
- `Access denied` - Permission error
- `Cannot remove directory` - Need -Recurse flag
- `Cannot move file` - Move operation failed
- `Cannot overwrite same file` - Source and destination are same

---

## 🏗️ Architecture

- **Session-based virtual filesystem** - Each WebSocket connection has isolated filesystem
- **Current working directory tracking** - Maintains CWD per session
- **Manual command parser** - Custom tokenizer (not real PowerShell)
- **Pipeline execution** - Sequential command execution with output passing
- **Environment variables** - Per-session environment storage

---

## 🎯 Use Cases

This enhanced PowerShell engine is suitable for:
- Windows administrator training and assessments
- Fresher/intermediate level technical interviews
- Executive demos of terminal automation
- Educational platforms teaching PowerShell basics
- Simulated Windows environments for testing
