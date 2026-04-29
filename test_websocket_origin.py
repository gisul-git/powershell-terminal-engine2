"""
Regression test for production WebSocket origins.
"""

from fastapi.testclient import TestClient

from main import app


def test_dev_origin_websocket_is_accepted():
    client = TestClient(app)

    with client.websocket_connect(
        "/terminal",
        headers={"Origin": "https://dev.aaptor.com"},
    ) as websocket:
        message = websocket.receive_json()

    assert message["type"] == "init"
    assert "prompt" in message["data"]


def test_qa_origin_websocket_is_accepted():
    client = TestClient(app)

    with client.websocket_connect(
        "/terminal",
        headers={"Origin": "https://qa.aaptor.com"},
    ) as websocket:
        message = websocket.receive_json()

    assert message["type"] == "init"
    assert "prompt" in message["data"]


if __name__ == "__main__":
    test_dev_origin_websocket_is_accepted()
    test_qa_origin_websocket_is_accepted()
    print("WebSocket origin regression tests passed")
