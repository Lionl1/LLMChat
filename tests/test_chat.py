"""Basic tests for the chat application."""

import pytest
from src.config.app_config import AppConfig

def test_app_config():
    """Test AppConfig initialization."""
    assert AppConfig.DEFAULT_MAX_TOKENS == 2048
    assert AppConfig.DEFAULT_TEMPERATURE == 0.1
    assert len(AppConfig.DEFAULT_SYSTEM_MESSAGE) == 2
    assert "en" in AppConfig.DEFAULT_SYSTEM_MESSAGE
    assert "ru" in AppConfig.DEFAULT_SYSTEM_MESSAGE

def test_language_support():
    """Test language support in configuration."""
    assert "en" in AppConfig.PLACEHOLDER_TEXT
    assert "ru" in AppConfig.PLACEHOLDER_TEXT
    assert "en" in AppConfig.THINKING_TEXT
    assert "ru" in AppConfig.THINKING_TEXT

def test_api_configuration():
    """Test API configuration."""
    assert AppConfig.API_URL.startswith("http")
    assert AppConfig.TIMEOUT > 0
    assert AppConfig.API_KEY_ENV_VAR == "API_KEY"

def test_chat_limits():
    """Test chat limitations."""
    assert AppConfig.MAX_HISTORY_LENGTH > 0
    assert AppConfig.MAX_CHATS > 0
