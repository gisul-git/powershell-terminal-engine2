"""
Enterprise-grade PowerShell Engine Demo
Showcases realistic Windows admin scenarios
"""
import asyncio
from session_manager import create_session
from execution_engine import execute_command


async def demo_scenario():
    session = create_session()
    
    print("=" * 70)
    print("  ENTERPRISE POWERSHELL ENGINE DEMO")
    print("  Advanced Administrative Commands & Pipeline Capabilities")
    print("=" * 70)
    
    # Scenario 1: Log Analysis
    print("\n" + "=" * 70)
    print("SCENARIO 1: System Log Analysis")
    print("=" * 70)
    
    print("\n→ Creating application log file...")
    await execute_command(session, "New-Item application.log -ItemType File")
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:15:23 INFO: Application started"')
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:15:45 ERROR: Database connection failed"')
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:16:12 WARNING: High memory usage detected"')
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:16:30 ERROR: Timeout on API call"')
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:17:01 INFO: Retry successful"')
    await execute_command(session, 'Add-Content application.log "2026-04-28 10:17:15 ERROR: Permission denied"')
    
    print("\n→ Analyzing errors in log file...")
    result = await execute_command(session, "Get-Content application.log | Select-String ERROR")
    print(f"\nErrors found:\n{result['output']}")
    
    print("\n→ Counting total errors...")
    result = await execute_command(session, "Get-Content application.log | Select-String ERROR | Measure-Object")
    print(f"\n{result['output']}")
    
    # Scenario 2: User Management
    print("\n" + "=" * 70)
    print("SCENARIO 2: User Account Management")
    print("=" * 70)
    
    print("\n→ Creating user database...")
    await execute_command(session, "New-Item users.csv -ItemType File")
    await execute_command(session, 'Add-Content users.csv "john.doe@company.com"')
    await execute_command(session, 'Add-Content users.csv "alice.smith@company.com"')
    await execute_command(session, 'Add-Content users.csv "bob.jones@company.com"')
    await execute_command(session, 'Add-Content users.csv "charlie.brown@company.com"')
    
    print("\n→ Sorting users alphabetically...")
    result = await execute_command(session, "Get-Content users.csv | Sort-Object")
    print(f"\nSorted users:\n{result['output']}")
    
    print("\n→ Getting top 2 users...")
    result = await execute_command(session, "Get-Content users.csv | Sort-Object | Select-Object -First 2")
    print(f"\nTop 2:\n{result['output']}")
    
    print("\n→ Renaming user database...")
    await execute_command(session, "Rename-Item users.csv active_users.csv")
    result = await execute_command(session, "dir")
    print(f"\nDirectory listing:\n{result['output']}")
    
    # Scenario 3: Environment Configuration
    print("\n" + "=" * 70)
    print("SCENARIO 3: Environment Configuration")
    print("=" * 70)
    
    print("\n→ Setting environment variables...")
    await execute_command(session, '$env:APP_NAME="EnterpriseApp"')
    await execute_command(session, '$env:APP_VERSION="2.5.1"')
    await execute_command(session, '$env:DB_HOST="sql-server-01.company.local"')
    await execute_command(session, '$env:LOG_LEVEL="DEBUG"')
    
    print("\n→ Viewing environment configuration...")
    result = await execute_command(session, "Get-ChildItem Env:")
    print(f"\n{result['output']}")
    
    print("\n→ Using 'set' command (CMD compatibility)...")
    result = await execute_command(session, "set")
    print(f"\n{result['output']}")
    
    # Scenario 4: Process Management
    print("\n" + "=" * 70)
    print("SCENARIO 4: Process Management & Analysis")
    print("=" * 70)
    
    print("\n→ Listing all processes...")
    result = await execute_command(session, "Get-Process")
    print(f"\n{result['output']}")
    
    print("\n→ Sorting processes by ID...")
    result = await execute_command(session, "Get-Process | Sort-Object Id")
    print(f"\n{result['output']}")
    
    print("\n→ Extracting process IDs only...")
    result = await execute_command(session, "Get-Process | Select-Object Id")
    print(f"\n{result['output']}")
    
    # Scenario 5: File Operations
    print("\n" + "=" * 70)
    print("SCENARIO 5: Advanced File Operations")
    print("=" * 70)
    
    print("\n→ Creating configuration file...")
    await execute_command(session, "New-Item config.ini -ItemType File")
    await execute_command(session, 'Set-Content config.ini "[Database]"')
    await execute_command(session, 'Add-Content config.ini "Host=localhost"')
    await execute_command(session, 'Add-Content config.ini "Port=5432"')
    
    print("\n→ Backing up configuration...")
    await execute_command(session, "Copy-Item config.ini config.backup.ini")
    
    print("\n→ Creating archive copy...")
    await execute_command(session, "Copy-Item config.ini config.archive.ini")
    
    print("\n→ Moving archive to different name...")
    await execute_command(session, "Move-Item config.archive.ini config.old.ini")
    
    result = await execute_command(session, "dir")
    print(f"\nFinal directory state:\n{result['output']}")
    
    # Scenario 6: System Information
    print("\n" + "=" * 70)
    print("SCENARIO 6: System Information Gathering")
    print("=" * 70)
    
    print("\n→ Current timestamp...")
    result = await execute_command(session, "Get-Date")
    print(f"\n{result['output']}")
    
    print("\n→ Current working directory...")
    result = await execute_command(session, "Get-Location")
    print(f"\n{result['output']}")
    
    print("\n→ Alternative: pwd command...")
    result = await execute_command(session, "pwd")
    print(f"\n{result['output']}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\n✓ Log analysis with filtering and counting")
    print("✓ User management with sorting and selection")
    print("✓ Environment variable configuration")
    print("✓ Process management and analysis")
    print("✓ Advanced file operations (copy, move, rename)")
    print("✓ System information retrieval")
    print("✓ Complex multi-stage pipelines")
    print("\nThe PowerShell engine is ready for enterprise use!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_scenario())
