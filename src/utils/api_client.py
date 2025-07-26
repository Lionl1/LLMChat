import requests
from typing import Dict, Any, Optional
from ..config.app_config import AppConfig

class ApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_response(self, messages: list) -> Optional[Dict[str, Any]]:
        """Get response from the local API with enhanced error handling"""
        try:
            # Format prompt with history
            prompt = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}" 
                for msg in messages
                if msg["role"] != "system"
            )
            
            # Add last user message if exists
            if messages and messages[-1]["role"] == "user":
                prompt += f"\nUser: {messages[-1]['content']}"
            
            data = {
                "model": AppConfig.DEFAULT_MODEL,
                "prompt": prompt,
                "max_tokens": AppConfig.DEFAULT_MAX_TOKENS,
                "temperature": AppConfig.DEFAULT_TEMPERATURE,
                "top_p": AppConfig.DEFAULT_TOP_P,
                "top_k": AppConfig.DEFAULT_TOP_K,
                "repetition_penalty": AppConfig.DEFAULT_REPETITION_PENALTY,
                "stream": False
            }
            
            response = requests.post(
                AppConfig.API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=data,
                timeout=AppConfig.TIMEOUT
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.Timeout:
            raise TimeoutError("Request timeout. Server not responding.")
        except requests.RequestException as e:
            raise ConnectionError(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Critical error: {str(e)}")
