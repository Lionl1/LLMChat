import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    # System configuration
    DEFAULT_SYSTEM_MESSAGE: Dict[str, str] = {
        "en": "You are a helpful AI assistant.",
        "ru": "Я - полезный ИИ-ассистент. Я говорю по-русски и стараюсь помогать людям."
    }
    
    # API configuration
    API_URL: str = os.getenv('API_URL')
    API_KEY_ENV_VAR: str = "API_KEY"
    TIMEOUT: int = int(os.getenv('API_TIMEOUT', '15'))
    DEFAULT_MODEL: str = os.getenv('MODEL_NAME')
    
    # Model parameters
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', '2048'))
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', '0.1'))
    DEFAULT_TOP_P: float = float(os.getenv('DEFAULT_TOP_P', '0.9'))
    DEFAULT_TOP_K: int = int(os.getenv('DEFAULT_TOP_K', '40'))
    DEFAULT_REPETITION_PENALTY: float = float(os.getenv('DEFAULT_REPETITION_PENALTY', '1.1'))
    
    # UI text
    PLACEHOLDER_TEXT: Dict[str, str] = {
        "ru": "Введите ваше сообщение...",
        "en": "Enter your message..."
    }
    THINKING_TEXT: Dict[str, str] = {
        "ru": "Думаю...",
        "en": "Thinking..."
    }
    
    # Chat settings
    CHATS_FILE: str = "saved_chats.json"
    MAX_HISTORY_LENGTH: int = 20
    MAX_CHATS: int = 50
