from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient

from src.config.app_config import AppConfig
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


def test_extract_ignores_client_supplied_service_url(client):
    with patch("src.server.extract_text_from_file", return_value=[]) as extract:
        client.post(
            "/api/extract",
            files={"files": ("a.txt", b"alpha")},
            data={"extract_api_url": "http://169.254.169.254/latest"},
        )
    assert extract.call_args.args[2] == AppConfig.EXTRACT_TEXT_API_URL
