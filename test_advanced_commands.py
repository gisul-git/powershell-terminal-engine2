"""
Test script for advanced Windows administration commands
"""
import asyncio
from session_manager import create_session
from execution_engine import execute_command


async def test_advanced_commands():
    session = create_session()
    
    print("=" * 70)
    print("Testing Advanced Windows Administration Commands")
    print("=" * 70)
    
    # Test 1: Get-ChildItem / dir / ls
    print("\n1. Testing Get-ChildItem / dir / ls...")
    await execute_command(session, "New-Item test1.txt -ItemType File")
    await execute_command(session, "New-Item test2.txt -ItemType File")
    await execute_command(session, "New-Item logs -ItemType Directory")
    
    result = await execute_command(session, "Get-ChildItem")
    print(f"Get-ChildItem:\n{result['output']}\n")
    
    result = await execute_command(session, "dir")
    print(f"dir:\n{result['output']}\n")
    
    result = await execute_command(session, "ls")
    print(f"ls:\n{result['output']}\n")
    
    # Test 2: Get-Item
    print("\n2. Testing Get-Item...")
    result = await execute_command(session, "Get-Item test1.txt")
    print(f"Get-Item test1.txt:\n{result['output']}\n")
    
    result = await execute_command(session, "Get-Item logs")
    print(f"Get-Item logs:\n{result['output']}\n")
    
    # Test 3: Test-Path
    print("\n3. Testing Test-Path...")
    result = await execute_command(session, "Test-Path test1.txt")
    print(f"Test-Path test1.txt: {result['output']}")
    
    result = await execute_command(session, "Test-Path nonexistent.txt")
    print(f"Test-Path nonexistent.txt: {result['output']}\n")
    
    # Test 4: Get-Service
    print("\n4. Testing Get-Service...")
    result = await execute_command(session, "Get-Service")
    print(f"Get-Service:\n{result['output']}\n")
    
    # Test 5: Start-Service
    print("\n5. Testing Start-Service...")
    await execute_command(session, "Start-Service WSearch")
    result = await execute_command(session, "Get-Service")
    print(f"After Start-Service WSearch:\n{result['output']}\n")
    
    # Test 6: Stop-Service
    print("\n6. Testing Stop-Service...")
    await execute_command(session, "Stop-Service Spooler")
    result = await execute_command(session, "Get-Service")
    print(f"After Stop-Service Spooler:\n{result['output']}\n")
    
    # Test 7: Restart-Service
    print("\n7. Testing Restart-Service...")
    await execute_command(session, "Restart-Service WinDefend")
    result = await execute_command(session, "Get-Service")
    print(f"After Restart-Service WinDefend:\n{result['output']}\n")
    
    # Test 8: Test-Connection
    print("\n8. Testing Test-Connection...")
    result = await execute_command(session, "Test-Connection google.com")
    print(f"Test-Connection google.com:\n{result['output']}\n")
    
    # Test 9: ipconfig
    print("\n9. Testing ipconfig...")
    result = await execute_command(session, "ipconfig")
    print(f"ipconfig:\n{result['output']}\n")
    
    # Test 10: Resolve-DnsName
    print("\n10. Testing Resolve-DnsName...")
    result = await execute_command(session, "Resolve-DnsName google.com")
    print(f"Resolve-DnsName google.com:\n{result['output']}\n")
    
    # Test 11: whoami
    print("\n11. Testing whoami...")
    result = await execute_command(session, "whoami")
    print(f"whoami: {result['output']}\n")
    
    # Test 12: hostname
    print("\n12. Testing hostname...")
    result = await execute_command(session, "hostname")
    print(f"hostname: {result['output']}\n")
    
    # Test 13: Get-ComputerInfo
    print("\n13. Testing Get-ComputerInfo...")
    result = await execute_command(session, "Get-ComputerInfo")
    print(f"Get-ComputerInfo:\n{result['output']}\n")
    
    # Test 14: Compress-Archive
    print("\n14. Testing Compress-Archive...")
    await execute_command(session, "New-Item data.txt -ItemType File")
    await execute_command(session, 'Set-Content data.txt "Important data"')
    await execute_command(session, "Compress-Archive data.txt backup.zip")
    result = await execute_command(session, "Get-ChildItem")
    print(f"After Compress-Archive:\n{result['output']}\n")
    
    # Test 15: Expand-Archive
    print("\n15. Testing Expand-Archive...")
    await execute_command(session, "Expand-Archive backup.zip restored.txt")
    result = await execute_command(session, "Get-Content restored.txt")
    print(f"Expanded content: {result['output']}\n")
    
    # Test 16: Where-Object
    print("\n16. Testing Where-Object...")
    result = await execute_command(session, "Get-Process | Where-Object Id -gt 101")
    print(f"Get-Process | Where-Object Id -gt 101:\n{result['output']}\n")
    
    # Test 17: ForEach-Object
    print("\n17. Testing ForEach-Object...")
    await execute_command(session, "New-Item items.txt -ItemType File")
    await execute_command(session, 'Add-Content items.txt "item1"')
    await execute_command(session, 'Add-Content items.txt "item2"')
    await execute_command(session, 'Add-Content items.txt "item3"')
    result = await execute_command(session, "Get-Content items.txt | ForEach-Object")
    print(f"Get-Content items.txt | ForEach-Object:\n{result['output']}\n")
    
    # Test 18: Complex Pipeline with Where-Object
    print("\n18. Testing complex pipeline with Where-Object...")
    result = await execute_command(session, "Get-ChildItem | Where-Object Name -eq test1.txt")
    print(f"Get-ChildItem | Where-Object Name -eq test1.txt:\n{result['output']}\n")
    
    # Test 19: Multi-stage pipeline
    print("\n19. Testing multi-stage pipeline...")
    result = await execute_command(session, "Get-Process | Sort-Object Id | Select-Object Id")
    print(f"Get-Process | Sort-Object Id | Select-Object Id:\n{result['output']}\n")
    
    print("=" * 70)
    print("All advanced command tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_advanced_commands())
