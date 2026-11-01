from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient

from src.server import app


@pytest.fixture
def client():
    return TestClient(app)


def chat_payload(**overrides):
    payload = {"messages": [{"role": "user", "content": "Hi"}]}
    payload.update(overrides)
    return payload


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_index_serves_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_config_exposes_defaults(client):
    data = client.get("/api/config").json()
    assert data["api_url"]
    assert set(data["params"]) == {"temperature", "max_tokens", "top_p"}


def test_chat_returns_model_message(client):
    reply = {"choices": [{"message": {"content": "  Hello!  "}}]}
    with patch("src.server.request_chat_completion", return_value=reply):
        response = client.post("/api/chat", json=chat_payload())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello!"}


def test_chat_accepts_completion_style_reply(client):
    with patch("src.server.request_chat_completion", return_value={"choices": [{"text": "ok"}]}):
        response = client.post("/api/chat", json=chat_payload())
    assert response.json() == {"message": "ok"}


def test_chat_empty_reply_is_bad_gateway(client):
    with patch("src.server.request_chat_completion", return_value={"choices": []}):
        response = client.post("/api/chat", json=chat_payload())
    assert response.status_code == 502


def test_chat_unreachable_model_is_bad_gateway(client):
    error = requests.ConnectionError("refused")
    with patch("src.server.request_chat_completion", side_effect=error):
        response = client.post("/api/chat", json=chat_payload())
    assert response.status_code == 502
    assert "refused" in response.json()["detail"]


def test_chat_rejects_out_of_range_params(client):
    response = client.post("/api/chat", json=chat_payload(params={"temperature": 5}))
    assert response.status_code == 422


def test_extract_combines_files(client):
    extracted = [{"filename": "a.txt", "text": "alpha"}]
    with patch("src.server.extract_text_from_file", return_value=extracted):
        response = client.post("/api/extract", files={"files": ("a.txt", b"alpha")})
    assert response.status_code == 200
    assert response.json()["text"] == "File: a.txt\nalpha"


def sent_api_key(client, monkeypatch, **payload):
    monkeypatch.setenv("API_KEY", "server-secret")
    reply = {"choices": [{"message": {"content": "ok"}}]}
    with patch("src.server.request_chat_completion", return_value=reply) as completion:
        client.post("/api/chat", json=chat_payload(**payload))
    return completion.call_args.kwargs["api_key"]


def test_server_key_is_used_for_configured_endpoint(client, monkeypatch):
    assert sent_api_key(client, monkeypatch) == "server-secret"


def test_server_key_is_not_sent_to_client_supplied_endpoint(client, monkeypatch):
    key = sent_api_key(client, monkeypatch, api_url="https://attacker.example/v1/chat/completions")
    assert not key


def test_client_key_is_forwarded_to_client_endpoint(client, monkeypatch):
    key = sent_api_key(
        client, monkeypatch, api_url="https://other.example/v1/chat/completions", api_key="mine"
    )
    assert key == "mine"
