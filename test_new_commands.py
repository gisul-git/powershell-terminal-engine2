"""
Test script for new PowerShell commands
"""
import asyncio
from session_manager import create_session
from execution_engine import execute_command


async def test_commands():
    session = create_session()
    
    print("=" * 60)
    print("Testing New PowerShell Commands")
    print("=" * 60)
    
    # Test 1: Create file and add content
    print("\n1. Creating users.txt and adding content...")
    await execute_command(session, "New-Item users.txt -ItemType File")
    await execute_command(session, 'Add-Content users.txt "charlie"')
    await execute_command(session, 'Add-Content users.txt "alice"')
    await execute_command(session, 'Add-Content users.txt "bob"')
    result = await execute_command(session, "Get-Content users.txt")
    print(f"Content:\n{result['output']}")
    
    # Test 2: Sort-Object
    print("\n2. Testing Sort-Object...")
    result = await execute_command(session, "Get-Content users.txt | Sort-Object")
    print(f"Sorted:\n{result['output']}")
    
    # Test 3: Measure-Object
    print("\n3. Testing Measure-Object...")
    result = await execute_command(session, "Get-Content users.txt | Measure-Object")
    print(f"Count:\n{result['output']}")
    
    # Test 4: Select-Object -First
    print("\n4. Testing Select-Object -First 2...")
    result = await execute_command(session, "Get-Content users.txt | Sort-Object | Select-Object -First 2")
    print(f"First 2:\n{result['output']}")
    
    # Test 5: Rename-Item
    print("\n5. Testing Rename-Item...")
    await execute_command(session, "Rename-Item users.txt members.txt")
    result = await execute_command(session, "dir")
    print(f"Directory:\n{result['output']}")
    
    # Test 6: Get-Date
    print("\n6. Testing Get-Date...")
    result = await execute_command(session, "Get-Date")
    print(f"Date:\n{result['output']}")
    
    # Test 7: Get-Location
    print("\n7. Testing Get-Location...")
    result = await execute_command(session, "Get-Location")
    print(f"Location:\n{result['output']}")
    
    # Test 8: Environment variables
    print("\n8. Testing environment variables...")
    await execute_command(session, '$env:TEST="HelloWorld"')
    await execute_command(session, '$env:PATH="C:\\Windows"')
    result = await execute_command(session, "Get-ChildItem Env:")
    print(f"Environment:\n{result['output']}")
    
    # Test 9: set command (alias)
    print("\n9. Testing 'set' command...")
    result = await execute_command(session, "set")
    print(f"Set output:\n{result['output']}")
    
    # Test 10: Copy-Item (alias test)
    print("\n10. Testing Copy-Item...")
    await execute_command(session, "New-Item test.txt -ItemType File")
    await execute_command(session, 'Set-Content test.txt "test content"')
    await execute_command(session, "Copy-Item test.txt test_copy.txt")
    result = await execute_command(session, "Get-Content test_copy.txt")
    print(f"Copied file content:\n{result['output']}")
    
    # Test 11: Move-Item (alias test)
    print("\n11. Testing Move-Item...")
    await execute_command(session, "Move-Item test_copy.txt moved.txt")
    result = await execute_command(session, "dir")
    print(f"After move:\n{result['output']}")
    
    # Test 12: Complex pipeline
    print("\n12. Testing complex pipeline...")
    await execute_command(session, "New-Item errors.log -ItemType File")
    await execute_command(session, 'Add-Content errors.log "INFO: Starting"')
    await execute_command(session, 'Add-Content errors.log "ERROR: Failed"')
    await execute_command(session, 'Add-Content errors.log "ERROR: Timeout"')
    result = await execute_command(session, "Get-Content errors.log | Select-String ERROR | Measure-Object")
    print(f"Pipeline result:\n{result['output']}")
    
    # Test 13: Get-Process with Sort and Select
    print("\n13. Testing Get-Process pipeline...")
    result = await execute_command(session, "Get-Process | Sort-Object Id | Select-Object Id")
    print(f"Process IDs:\n{result['output']}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_commands())
