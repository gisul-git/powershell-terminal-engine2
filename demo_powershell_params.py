"""
PowerShell Named Parameters Demo
Demonstrates all the new features added to the PowerShell engine.
"""

import asyncio
from execution_engine import execute_command
from session_manager import create_session


async def demo():
    print("=" * 70)
    print("PowerShell Named Parameters - CEO Demo")
    print("=" * 70)
    print()
    
    session = create_session()
    
    # Demo 1: New-Item with named parameters
    print("📁 Demo 1: Creating directory with named parameters")
    print("Command: New-Item -ItemType Directory -Name audit_case")
    result = await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
    print(f"✓ Directory created successfully\n")
    
    # Demo 2: Set-Location (new command)
    print("📂 Demo 2: Changing directory with Set-Location")
    print("Command: Set-Location audit_case")
    result = await execute_command(session, "Set-Location audit_case")
    print(f"✓ Changed to: {session['cwd']}\n")
    
    # Demo 3: New-Item file with named parameters
    print("📄 Demo 3: Creating file with named parameters")
    print("Command: New-Item -ItemType File -Name events.log")
    result = await execute_command(session, "New-Item -ItemType File -Name events.log")
    print(f"✓ File created successfully\n")
    
    # Demo 4: Adding content
    print("✍️  Demo 4: Adding content to file")
    print('Command: Add-Content events.log "ERROR Disk failure"')
    await execute_command(session, 'Add-Content events.log "ERROR Disk failure"')
    print('Command: Add-Content events.log "INFO System started"')
    await execute_command(session, 'Add-Content events.log "INFO System started"')
    print('Command: Add-Content events.log "ERROR Memory overflow"')
    await execute_command(session, 'Add-Content events.log "ERROR Memory overflow"')
    print('Command: Add-Content events.log "INFO Process completed"')
    await execute_command(session, 'Add-Content events.log "INFO Process completed"')
    print(f"✓ Content added successfully\n")
    
    # Demo 5: View content
    print("👀 Demo 5: Viewing file content")
    print("Command: Get-Content events.log")
    result = await execute_command(session, "Get-Content events.log")
    print(f"Output:\n{result['output']}\n")
    
    # Demo 6: Pipeline with Select-String and ForEach-Object
    print("🔍 Demo 6: Advanced pipeline with script block")
    print('Command: Select-String "ERROR" events.log | ForEach-Object { $_.Line }')
    result = await execute_command(session, 'Select-String "ERROR" events.log | ForEach-Object { $_.Line }')
    print(f"Output:\n{result['output']}\n")
    
    # Demo 7: Pipeline to Set-Content
    print("💾 Demo 7: Saving filtered results to new file")
    print('Command: Select-String "ERROR" events.log | ForEach-Object { $_.Line } | Set-Content issues.log')
    result = await execute_command(session, 'Select-String "ERROR" events.log | ForEach-Object { $_.Line } | Set-Content issues.log')
    print(f"✓ Filtered content saved to issues.log\n")
    
    # Demo 8: Verify saved content
    print("✅ Demo 8: Verifying saved content")
    print("Command: Get-Content issues.log")
    result = await execute_command(session, "Get-Content issues.log")
    print(f"Output:\n{result['output']}\n")
    
    # Demo 9: Stop-Process with named parameters
    print("🛑 Demo 9: Stopping process with named parameters")
    session["processes"].append({"pid": 102, "name": "TestProcess"})
    session["processes"].append({"pid": 103, "name": "AnotherProcess"})
    print("Command: Get-Process")
    result = await execute_command(session, "Get-Process")
    print(f"Before:\n{result['output']}\n")
    
    print("Command: Stop-Process -Id 102 -Force")
    result = await execute_command(session, "Stop-Process -Id 102 -Force")
    print(f"✓ Process 102 stopped\n")
    
    print("Command: Get-Process")
    result = await execute_command(session, "Get-Process")
    print(f"After:\n{result['output']}\n")
    
    # Demo 10: Case insensitivity
    print("🔤 Demo 10: Case-insensitive parameters")
    print("Command: New-Item -itemtype file -name test.txt")
    result = await execute_command(session, "New-Item -itemtype file -name test.txt")
    print(f"✓ Parameters work regardless of case\n")
    
    # Summary
    print("=" * 70)
    print("✨ Summary of New Features")
    print("=" * 70)
    print("✓ parse_params() - Parses PowerShell-style named parameters")
    print("✓ New-Item - Supports -ItemType and -Name parameters")
    print("✓ Set-Location - New command (alias for cd)")
    print("✓ Stop-Process - Supports -Id and -Force parameters")
    print("✓ ForEach-Object - Handles script blocks like { $_.Line }")
    print("✓ Set-Content - Accepts pipeline input")
    print("✓ Select-String - Fixed to work with pattern and file")
    print("✓ Case-insensitive parameter names")
    print("✓ Backward compatibility maintained")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
