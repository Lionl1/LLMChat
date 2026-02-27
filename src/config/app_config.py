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
    API_URL: str = os.getenv('API_URL', 'http://localhost:8000/v1/chat/completions')
    API_KEY_ENV_VAR: str = "API_KEY"
    TIMEOUT: int = int(os.getenv('API_TIMEOUT', '15'))
    DEFAULT_MODEL: str = os.getenv('MODEL_NAME', 'local-model')

    # Extract-text service configuration
    EXTRACT_TEXT_API_URL: str = os.getenv('EXTRACT_TEXT_API_URL', 'http://localhost:7555')
    EXTRACT_TEXT_TIMEOUT: int = int(os.getenv('EXTRACT_TEXT_TIMEOUT', '120'))
    MAX_IMPORTED_CHARS: int = int(os.getenv('MAX_IMPORTED_CHARS', '20000'))
    
    # Model parameters
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', '2048'))
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', '0.1'))
    DEFAULT_TOP_P: float = float(os.getenv('DEFAULT_TOP_P', '0.9'))
