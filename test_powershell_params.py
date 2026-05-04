"""
Test PowerShell-style named parameters upgrade.
Tests all new features: parse_params, New-Item, Set-Location, Stop-Process, pipeline fixes.
"""

import asyncio
import pytest
from execution_engine import execute_command, parse_params
from session_manager import create_session


@pytest.fixture
def session():
    """Create a fresh session for each test."""
    return create_session()


class TestParseParams:
    """Test the parse_params function."""
    
    def test_parse_simple_params(self):
        args = ["-ItemType", "Directory", "-Name", "audit_case"]
        params = parse_params(args)
        assert params == {"ItemType": "Directory", "Name": "audit_case"}
    
    def test_parse_flag_params(self):
        args = ["-Id", "102", "-Force"]
        params = parse_params(args)
        assert params == {"Id": "102", "Force": True}
    
    def test_parse_mixed_params(self):
        args = ["positional", "-ItemType", "File", "-Name", "events.log"]
        params = parse_params(args)
        assert params == {"ItemType": "File", "Name": "events.log"}
    
    def test_parse_empty(self):
        params = parse_params([])
        assert params == {}
    
    def test_parse_quoted_values(self):
        args = ["-Name", '"my file.txt"', "-ItemType", "'Directory'"]
        params = parse_params(args)
        assert params == {"Name": "my file.txt", "ItemType": "Directory"}


class TestNewItemWithParams:
    """Test New-Item with named parameters."""
    
    @pytest.mark.asyncio
    async def test_new_item_directory_with_params(self, session):
        result = await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
        assert result["output"] == ""
        assert "C:\\Users\\User\\audit_case" in session["fs"]
        assert session["fs"]["C:\\Users\\User\\audit_case"]["type"] == "dir"
    
    @pytest.mark.asyncio
    async def test_new_item_file_with_params(self, session):
        result = await execute_command(session, "New-Item -ItemType File -Name events.log")
        assert result["output"] == ""
        assert "C:\\Users\\User\\events.log" in session["fs"]
        assert session["fs"]["C:\\Users\\User\\events.log"]["type"] == "file"
    
    @pytest.mark.asyncio
    async def test_new_item_case_insensitive(self, session):
        result = await execute_command(session, "New-Item -itemtype directory -name test_dir")
        assert result["output"] == ""
        assert "C:\\Users\\User\\test_dir" in session["fs"]
    
    @pytest.mark.asyncio
    async def test_new_item_missing_params(self, session):
        result = await execute_command(session, "New-Item -ItemType Directory")
        assert "Invalid arguments" in result["output"]
    
    @pytest.mark.asyncio
    async def test_new_item_legacy_still_works(self, session):
        # Ensure backward compatibility
        result = await execute_command(session, "New-Item test_legacy -ItemType Directory")
        assert result["output"] == ""
        assert "C:\\Users\\User\\test_legacy" in session["fs"]


class TestSetLocation:
    """Test Set-Location command (alias for cd)."""
    
    @pytest.mark.asyncio
    async def test_set_location_basic(self, session):
        await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
        result = await execute_command(session, "Set-Location audit_case")
        assert result["output"] == ""
        assert session["cwd"] == "C:\\Users\\User\\audit_case"
    
    @pytest.mark.asyncio
    async def test_set_location_absolute_path(self, session):
        result = await execute_command(session, "Set-Location C:\\")
        assert result["output"] == ""
        assert session["cwd"] == "C:\\"
    
    @pytest.mark.asyncio
    async def test_set_location_nonexistent(self, session):
        result = await execute_command(session, "Set-Location nonexistent")
        assert "path" in result["output"].lower() or "exist" in result["output"].lower()
    
    @pytest.mark.asyncio
    async def test_set_location_home(self, session):
        result = await execute_command(session, "Set-Location")
        assert result["output"] == ""
        assert session["cwd"] == "C:\\Users\\User"


class TestStopProcessWithParams:
    """Test Stop-Process with named parameters."""
    
    @pytest.mark.asyncio
    async def test_stop_process_with_id_param(self, session):
        # Add a test process
        session["processes"].append({"pid": 102, "name": "TestProcess"})
        
        result = await execute_command(session, "Stop-Process -Id 102")
        assert result["output"] == ""
        assert not any(p["pid"] == 102 for p in session["processes"])
    
    @pytest.mark.asyncio
    async def test_stop_process_with_force_flag(self, session):
        session["processes"].append({"pid": 102, "name": "TestProcess"})
        
        result = await execute_command(session, "Stop-Process -Id 102 -Force")
        assert result["output"] == ""
        assert not any(p["pid"] == 102 for p in session["processes"])
    
    @pytest.mark.asyncio
    async def test_stop_process_legacy_still_works(self, session):
        session["processes"].append({"pid": 102, "name": "TestProcess"})
        
        result = await execute_command(session, "Stop-Process 102")
        assert result["output"] == ""
        assert not any(p["pid"] == 102 for p in session["processes"])
    
    @pytest.mark.asyncio
    async def test_stop_process_nonexistent(self, session):
        result = await execute_command(session, "Stop-Process -Id 999")
        assert "not found" in result["output"].lower() or "missing" in result["output"].lower()
    
    @pytest.mark.asyncio
    async def test_stop_process_invalid_id(self, session):
        result = await execute_command(session, "Stop-Process -Id abc")
        assert "Invalid arguments" in result["output"]


class TestPipelineWithScriptBlock:
    """Test pipeline with ForEach-Object and script blocks."""
    
    @pytest.mark.asyncio
    async def test_select_string_foreach_object(self, session):
        # Create file with content
        await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
        await execute_command(session, "Set-Location audit_case")
        await execute_command(session, "New-Item -ItemType File -Name events.log")
        await execute_command(session, 'Add-Content events.log "ERROR Disk failure"')
        await execute_command(session, 'Add-Content events.log "INFO System started"')
        await execute_command(session, 'Add-Content events.log "ERROR Memory overflow"')
        
        # Test pipeline: Select-String | ForEach-Object { $_.Line }
        result = await execute_command(
            session, 
            'Select-String "ERROR" events.log | ForEach-Object { $_.Line }'
        )
        
        assert "ERROR Disk failure" in result["output"]
        assert "ERROR Memory overflow" in result["output"]
        assert "INFO System started" not in result["output"]
    
    @pytest.mark.asyncio
    async def test_pipeline_to_set_content(self, session):
        # Create directory and files
        await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
        await execute_command(session, "Set-Location audit_case")
        await execute_command(session, "New-Item -ItemType File -Name events.log")
        await execute_command(session, 'Add-Content events.log "ERROR Disk"')
        await execute_command(session, 'Add-Content events.log "ERROR Memory"')
        
        # Full pipeline: Select-String | ForEach-Object | Set-Content
        result = await execute_command(
            session,
            'Select-String "ERROR" events.log | ForEach-Object { $_.Line } | Set-Content issues.log'
        )
        
        assert result["output"] == ""
        
        # Verify issues.log was created with correct content
        content_result = await execute_command(session, "Get-Content issues.log")
        assert "ERROR Disk" in content_result["output"]
        assert "ERROR Memory" in content_result["output"]


class TestCompleteScenario:
    """Test the complete CEO demo scenario."""
    
    @pytest.mark.asyncio
    async def test_complete_ceo_demo(self, session):
        # Step 1: Create directory
        result = await execute_command(session, "New-Item -ItemType Directory -Name audit_case")
        assert result["output"] == ""
        
        # Step 2: Change to directory
        result = await execute_command(session, "Set-Location audit_case")
        assert result["output"] == ""
        assert session["cwd"] == "C:\\Users\\User\\audit_case"
        
        # Step 3: Create file
        result = await execute_command(session, "New-Item -ItemType File -Name events.log")
        assert result["output"] == ""
        
        # Step 4: Add content
        result = await execute_command(session, 'Add-Content events.log "ERROR Disk"')
        assert result["output"] == ""
        
        result = await execute_command(session, 'Add-Content events.log "ERROR Memory"')
        assert result["output"] == ""
        
        # Step 5: Pipeline to filter and save
        result = await execute_command(
            session,
            'Select-String "ERROR" events.log | ForEach-Object { $_.Line } | Set-Content issues.log'
        )
        assert result["output"] == ""
        
        # Step 6: Verify content
        result = await execute_command(session, "Get-Content issues.log")
        assert "ERROR Disk" in result["output"]
        assert "ERROR Memory" in result["output"]
        
        # Step 7: Stop process
        session["processes"].append({"pid": 102, "name": "TestProcess"})
        result = await execute_command(session, "Stop-Process -Id 102 -Force")
        assert result["output"] == ""
        assert not any(p["pid"] == 102 for p in session["processes"])


class TestErrorHandling:
    """Test error handling for invalid commands."""
    
    @pytest.mark.asyncio
    async def test_new_item_no_itemtype(self, session):
        result = await execute_command(session, "New-Item -Name test")
        assert "Invalid arguments" in result["output"]
    
    @pytest.mark.asyncio
    async def test_new_item_no_name(self, session):
        result = await execute_command(session, "New-Item -ItemType Directory")
        assert "Invalid arguments" in result["output"]
    
    @pytest.mark.asyncio
    async def test_stop_process_no_id(self, session):
        result = await execute_command(session, "Stop-Process -Force")
        assert "Invalid arguments" in result["output"]
    
    @pytest.mark.asyncio
    async def test_set_location_too_many_args(self, session):
        result = await execute_command(session, "Set-Location path1 path2")
        assert "Invalid arguments" in result["output"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
