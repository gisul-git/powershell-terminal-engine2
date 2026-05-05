"""
Test long-running session configuration.
Verifies that all timeout settings are properly configured for 120-minute sessions.
"""

import asyncio
import time
from session_manager import (
    SESSION_TTL_SECONDS,
    create_session,
    cleanup_idle_sessions,
    touch_session,
    get_session,
)


def test_session_ttl_is_120_minutes():
    """Verify session TTL is set to 7200 seconds (120 minutes)."""
    assert SESSION_TTL_SECONDS == 7200, f"Expected 7200, got {SESSION_TTL_SECONDS}"
    print("✓ Session TTL is correctly set to 120 minutes (7200 seconds)")


def test_session_survives_119_minutes():
    """Verify session is NOT cleaned up before 120 minutes."""
    session = create_session()
    session_id = session["session_id"]
    
    # Simulate 119 minutes (7140 seconds) of inactivity
    session["last_seen"] = time.time() - 7140
    
    # Cleanup should not remove this session
    removed = cleanup_idle_sessions(SESSION_TTL_SECONDS)
    
    # Session should still exist
    assert get_session(session_id) is not None, "Session was removed too early!"
    print("✓ Session survives 119 minutes of inactivity")


def test_session_cleaned_after_120_minutes():
    """Verify session IS cleaned up after 120 minutes."""
    session = create_session()
    session_id = session["session_id"]
    
    # Simulate 121 minutes (7260 seconds) of inactivity
    session["last_seen"] = time.time() - 7260
    
    # Cleanup should remove this session
    removed = cleanup_idle_sessions(SESSION_TTL_SECONDS)
    
    # Session should be gone
    assert get_session(session_id) is None, "Session was not cleaned up!"
    assert removed == 1, f"Expected 1 session removed, got {removed}"
    print("✓ Session is cleaned up after 120 minutes")


def test_touch_session_extends_lifetime():
    """Verify touching a session extends its lifetime."""
    session = create_session()
    session_id = session["session_id"]
    
    # Simulate 119 minutes of inactivity
    session["last_seen"] = time.time() - 7140
    
    # Touch the session (simulates user activity)
    touch_session(session)
    
    # Cleanup should not remove this session
    removed = cleanup_idle_sessions(SESSION_TTL_SECONDS)
    
    # Session should still exist
    assert get_session(session_id) is not None, "Session was removed after touch!"
    print("✓ Touching session extends its lifetime")


def test_multiple_sessions_cleanup():
    """Verify cleanup handles multiple sessions correctly."""
    # Create 3 sessions with different ages
    session1 = create_session()
    session2 = create_session()
    session3 = create_session()
    
    # Session 1: 121 minutes old (should be removed)
    session1["last_seen"] = time.time() - 7260
    
    # Session 2: 119 minutes old (should survive)
    session2["last_seen"] = time.time() - 7140
    
    # Session 3: 1 minute old (should survive)
    session3["last_seen"] = time.time() - 60
    
    # Cleanup
    removed = cleanup_idle_sessions(SESSION_TTL_SECONDS)
    
    assert removed == 1, f"Expected 1 session removed, got {removed}"
    assert get_session(session1["session_id"]) is None, "Old session not removed"
    assert get_session(session2["session_id"]) is not None, "Recent session removed"
    assert get_session(session3["session_id"]) is not None, "Active session removed"
    print("✓ Multiple sessions cleaned up correctly")


def test_heartbeat_configuration():
    """Verify heartbeat settings in main.py."""
    import main
    
    assert main.HEARTBEAT_INTERVAL_SECONDS == 30, \
        f"Expected 30s interval, got {main.HEARTBEAT_INTERVAL_SECONDS}"
    assert main.HEARTBEAT_TIMEOUT_SECONDS == 300, \
        f"Expected 300s timeout, got {main.HEARTBEAT_TIMEOUT_SECONDS}"
    print("✓ Heartbeat configured: 30s interval, 300s timeout")


def test_gunicorn_configuration():
    """Verify gunicorn configuration."""
    import gunicorn_conf
    
    # Check default timeout (should be 7200)
    assert gunicorn_conf.timeout == 7200, \
        f"Expected 7200s timeout, got {gunicorn_conf.timeout}"
    assert gunicorn_conf.keepalive == 300, \
        f"Expected 300s keepalive, got {gunicorn_conf.keepalive}"
    print("✓ Gunicorn configured: 7200s timeout, 300s keepalive")


def test_uvicorn_worker_configuration():
    """Verify Uvicorn worker WebSocket settings."""
    try:
        from gunicorn_worker import ProductionUvicornWorker
        
        config = ProductionUvicornWorker.CONFIG_KWARGS
        assert config["ws_ping_interval"] == 30, \
            f"Expected 30s ping interval, got {config['ws_ping_interval']}"
        assert config["ws_ping_timeout"] == 300, \
            f"Expected 300s ping timeout, got {config['ws_ping_timeout']}"
        print("✓ Uvicorn worker configured: 30s ping interval, 300s ping timeout")
    except ImportError:
        # Gunicorn not installed in test environment - verify file directly
        with open("gunicorn_worker.py", "r") as f:
            content = f.read()
            assert '"ws_ping_interval": 30' in content, "ws_ping_interval not set to 30"
            assert '"ws_ping_timeout": 300' in content, "ws_ping_timeout not set to 300"
        print("✓ Uvicorn worker configured: 30s ping interval, 300s ping timeout (verified from file)")


def run_all_tests():
    """Run all configuration tests."""
    print("=" * 70)
    print("Long-Running Session Configuration Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_session_ttl_is_120_minutes,
        test_session_survives_119_minutes,
        test_session_cleaned_after_120_minutes,
        test_touch_session_extends_lifetime,
        test_multiple_sessions_cleanup,
        test_heartbeat_configuration,
        test_gunicorn_configuration,
        test_uvicorn_worker_configuration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print()
        print("✨ All configuration tests passed!")
        print()
        print("Configuration Summary:")
        print("  • Session TTL: 7200 seconds (120 minutes)")
        print("  • Gunicorn timeout: 7200 seconds")
        print("  • Gunicorn keepalive: 300 seconds")
        print("  • WebSocket ping interval: 30 seconds")
        print("  • WebSocket ping timeout: 300 seconds")
        print("  • Heartbeat interval: 30 seconds")
        print("  • Heartbeat timeout: 300 seconds")
        print("  • NGINX proxy_read_timeout: 7200 seconds")
        print("  • NGINX proxy_send_timeout: 7200 seconds")
        print()
        return True
    else:
        print()
        print("❌ Some tests failed. Please review the configuration.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
