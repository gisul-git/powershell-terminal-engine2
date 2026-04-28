"""
Test edge cases for new PowerShell commands
"""
import asyncio
from session_manager import create_session
from execution_engine import execute_command


async def test_edge_cases():
    session = create_session()
    
    print("=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    # Test 1: Measure-Object with empty input
    print("\n1. Measure-Object with empty input...")
    result = await execute_command(session, "echo | Measure-Object")
    print(f"Result: {result['output']}")
    
    # Test 2: Sort-Object with empty input
    print("\n2. Sort-Object with empty input...")
    result = await execute_command(session, "echo | Sort-Object")
    print(f"Result: '{result['output']}'")
    
    # Test 3: Rename non-existent file
    print("\n3. Rename non-existent file...")
    result = await execute_command(session, "Rename-Item nonexistent.txt new.txt")
    print(f"Error: {result['output']}")
    
    # Test 4: Rename with invalid arguments
    print("\n4. Rename with too few arguments...")
    result = await execute_command(session, "Rename-Item onlyone")
    print(f"Error: {result['output']}")
    
    # Test 5: Get-Date with arguments (should fail)
    print("\n5. Get-Date with arguments...")
    result = await execute_command(session, "Get-Date extra")
    print(f"Error: {result['output']}")
    
    # Test 6: Get-Location with arguments (should fail)
    print("\n6. Get-Location with arguments...")
    result = await execute_command(session, "Get-Location extra")
    print(f"Error: {result['output']}")
    
    # Test 7: Empty environment
    print("\n7. Get-ChildItem Env: with no variables...")
    result = await execute_command(session, "Get-ChildItem Env:")
    print(f"Result:\n{result['output']}")
    
    # Test 8: Triple pipeline
    print("\n8. Triple pipeline test...")
    await execute_command(session, "New-Item data.txt -ItemType File")
    await execute_command(session, 'Add-Content data.txt "zebra"')
    await execute_command(session, 'Add-Content data.txt "apple"')
    await execute_command(session, 'Add-Content data.txt "banana"')
    await execute_command(session, 'Add-Content data.txt "cherry"')
    result = await execute_command(session, "Get-Content data.txt | Sort-Object | Select-Object -First 2 | Measure-Object")
    print(f"Result: {result['output']}")
    
    # Test 9: Rename to existing file
    print("\n9. Rename to existing file name...")
    await execute_command(session, "New-Item file1.txt -ItemType File")
    await execute_command(session, "New-Item file2.txt -ItemType File")
    result = await execute_command(session, "Rename-Item file1.txt file2.txt")
    print(f"Error: {result['output']}")
    
    # Test 10: Select-Object with no property
    print("\n10. Select-Object without property...")
    result = await execute_command(session, "Get-Content data.txt | Select-Object")
    print(f"Result:\n{result['output']}")
    
    print("\n" + "=" * 60)
    print("Edge case tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_edge_cases())
