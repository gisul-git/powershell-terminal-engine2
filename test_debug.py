import asyncio
from execution_engine import execute_command
from session_manager import create_session

async def main():
    session = create_session()
    
    # Create directory and file
    result = await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
    print(f"Create dir: {result}")
    
    result = await execute_command(session, "Set-Location audit_case")
    print(f"Set-Location: {result}")
    
    result = await execute_command(session, "New-Item -ItemType File -Name events.log")
    print(f"Create file: {result}")
    
    result = await execute_command(session, 'Add-Content events.log "ERROR Disk"')
    print(f"Add content 1: {result}")
    
    result = await execute_command(session, 'Add-Content events.log "ERROR Memory"')
    print(f"Add content 2: {result}")
    
    result = await execute_command(session, 'Get-Content events.log')
    print(f"Get-Content: {result}")
    
    result = await execute_command(session, 'Select-String "ERROR" events.log')
    print(f"Select-String: {result}")
    
    result = await execute_command(session, 'Select-String "ERROR" events.log | ForEach-Object { $_.Line }')
    print(f"Pipeline: {result}")
    
    result = await execute_command(session, 'Select-String "ERROR" events.log | Set-Content issues.log')
    print(f"Pipeline to Set-Content: {result}")
    
    result = await execute_command(session, 'Get-Content issues.log')
    print(f"Get issues.log: {result}")

if __name__ == "__main__":
    asyncio.run(main())
