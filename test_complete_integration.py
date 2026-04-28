"""
Complete Integration Test - All Commands
Tests the entire PowerShell engine with all features
"""
import asyncio
from session_manager import create_session
from execution_engine import execute_command


async def test_complete_integration():
    session = create_session()
    
    print("=" * 80)
    print("COMPLETE INTEGRATION TEST - ALL FEATURES")
    print("=" * 80)
    
    test_count = 0
    pass_count = 0
    
    # Test 1: File System Commands
    print("\n[TEST 1] File System Commands...")
    test_count += 1
    try:
        await execute_command(session, "New-Item test.txt -ItemType File")
        result = await execute_command(session, "Test-Path test.txt")
        assert result['output'] == "True"
        result = await execute_command(session, "Get-Item test.txt")
        assert "test.txt" in result['output']
        result = await execute_command(session, "Get-ChildItem")
        assert "test.txt" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 2: Service Management
    print("\n[TEST 2] Service Management...")
    test_count += 1
    try:
        result = await execute_command(session, "Get-Service")
        assert "Spooler" in result['output']
        await execute_command(session, "Start-Service WSearch")
        result = await execute_command(session, "Get-Service")
        assert "Running  WSearch" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 3: Network Commands
    print("\n[TEST 3] Network Commands...")
    test_count += 1
    try:
        result = await execute_command(session, "ipconfig")
        assert "192.168.1.10" in result['output']
        result = await execute_command(session, "Test-Connection google.com")
        assert "Reply from google.com" in result['output']
        result = await execute_command(session, "Resolve-DnsName google.com")
        assert "google.com" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 4: System Information
    print("\n[TEST 4] System Information...")
    test_count += 1
    try:
        result = await execute_command(session, "whoami")
        assert result['output'] == "User"
        result = await execute_command(session, "hostname")
        assert result['output'] == "WIN-SERVER01"
        result = await execute_command(session, "Get-ComputerInfo")
        assert "Windows Server" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 5: Archive Operations
    print("\n[TEST 5] Archive Operations...")
    test_count += 1
    try:
        await execute_command(session, "New-Item data.txt -ItemType File")
        await execute_command(session, 'Set-Content data.txt "test data"')
        await execute_command(session, "Compress-Archive data.txt archive.zip")
        result = await execute_command(session, "Test-Path archive.zip")
        assert result['output'] == "True"
        await execute_command(session, "Expand-Archive archive.zip restored.txt")
        result = await execute_command(session, "Get-Content restored.txt")
        assert result['output'] == "test data"
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 6: Pipeline Operations
    print("\n[TEST 6] Pipeline Operations...")
    test_count += 1
    try:
        result = await execute_command(session, "Get-Process | Where-Object Id -gt 101")
        assert "102" in result['output']
        result = await execute_command(session, "Get-Process | Sort-Object Id | Select-Object Id")
        assert "101" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 7: Complex Workflows
    print("\n[TEST 7] Complex Workflows...")
    test_count += 1
    try:
        await execute_command(session, "New-Item log.txt -ItemType File")
        await execute_command(session, 'Add-Content log.txt "INFO: Start"')
        await execute_command(session, 'Add-Content log.txt "ERROR: Failed"')
        await execute_command(session, 'Add-Content log.txt "ERROR: Timeout"')
        result = await execute_command(session, "Get-Content log.txt | Select-String ERROR | Measure-Object")
        assert "Count : 2" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 8: Aliases
    print("\n[TEST 8] Command Aliases...")
    test_count += 1
    try:
        result1 = await execute_command(session, "dir")
        result2 = await execute_command(session, "ls")
        result3 = await execute_command(session, "Get-ChildItem")
        assert "test.txt" in result1['output']
        assert "test.txt" in result2['output']
        assert "test.txt" in result3['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 9: Environment Variables
    print("\n[TEST 9] Environment Variables...")
    test_count += 1
    try:
        await execute_command(session, '$env:TEST="value"')
        result = await execute_command(session, "Get-ChildItem Env:")
        assert "TEST" in result['output']
        result = await execute_command(session, "set")
        assert "TEST" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 10: Error Handling
    print("\n[TEST 10] Error Handling...")
    test_count += 1
    try:
        result = await execute_command(session, "Test-Path nonexistent.txt")
        assert result['output'] == "False"
        result = await execute_command(session, "Get-Item nonexistent.txt")
        assert "Item not found" in result['output']
        result = await execute_command(session, "Start-Service InvalidService")
        assert "Service not found" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 11: Multi-Stage Pipelines
    print("\n[TEST 11] Multi-Stage Pipelines...")
    test_count += 1
    try:
        await execute_command(session, "New-Item users.txt -ItemType File")
        await execute_command(session, 'Add-Content users.txt "charlie"')
        await execute_command(session, 'Add-Content users.txt "alice"')
        await execute_command(session, 'Add-Content users.txt "bob"')
        result = await execute_command(session, "Get-Content users.txt | Sort-Object | Select-Object -First 2 | Measure-Object")
        assert "Count : 2" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Test 12: Service State Persistence
    print("\n[TEST 12] Service State Persistence...")
    test_count += 1
    try:
        await execute_command(session, "Stop-Service Spooler")
        result = await execute_command(session, "Get-Service")
        assert "Stopped  Spooler" in result['output']
        await execute_command(session, "Restart-Service Spooler")
        result = await execute_command(session, "Get-Service")
        assert "Running  Spooler" in result['output']
        print("✓ PASS")
        pass_count += 1
    except Exception as e:
        print(f"✗ FAIL: {e}")
    
    # Final Results
    print("\n" + "=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    print(f"\nTotal Tests: {test_count}")
    print(f"Passed: {pass_count}")
    print(f"Failed: {test_count - pass_count}")
    print(f"Success Rate: {(pass_count/test_count)*100:.1f}%")
    
    if pass_count == test_count:
        print("\n✅ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
    else:
        print(f"\n⚠️ {test_count - pass_count} TEST(S) FAILED - REVIEW REQUIRED")
    
    print("=" * 80)
    
    return pass_count == test_count


if __name__ == "__main__":
    success = asyncio.run(test_complete_integration())
    exit(0 if success else 1)
