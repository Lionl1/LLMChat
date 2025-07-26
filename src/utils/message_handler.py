"""Message handling module."""

from typing import List, Dict
import os
import requests
import streamlit as st
from time import time

from config.app_config import AppConfig

def trim_message_history(messages: List[Dict]) -> List[Dict]:
    """Trim message history to avoid excessive memory usage."""
    system_message = [msg for msg in messages if msg["role"] == "system"]
    other_messages = [msg for msg in messages if msg["role"] != "system"]
    
    return system_message + other_messages[-AppConfig.MAX_HISTORY_LENGTH:]

def get_model_response(messages: list) -> Dict:
    """Get response from the local API with enhanced error handling."""
    try:
        api_key = os.getenv(AppConfig.API_KEY_ENV_VAR)
        if not api_key:
            st.error(f"API key not found. Set the '{AppConfig.API_KEY_ENV_VAR}' environment variable.")
            return None
            
        prompt = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" 
            for msg in messages
            if msg["role"] != "system"
        )
        
        if messages and messages[-1]["role"] == "user":
            prompt += f"\nUser: {messages[-1]['content']}"
        
        params = st.session_state.model_params
        data = {
            "model": AppConfig.DEFAULT_MODEL,
            "prompt": prompt,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "top_p": params["top_p"],
            "top_k": params["top_k"],
            "repetition_penalty": params["repetition_penalty"],
            "stream": False
        }
        
        response = requests.post(
            AppConfig.API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json=data,
            timeout=AppConfig.TIMEOUT
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.Timeout:
        st.error("Request timeout. Server not responding.")
    except requests.RequestException as e:
        st.error(f"Network error: {str(e)}")
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
    return None

def rate_limit_check() -> bool:
    """Basic rate limiting."""
    current_time = time()
    if 'last_request_time' not in st.session_state:
        st.session_state.last_request_time = current_time
        return True
        
    if current_time - st.session_state.last_request_time < 1.0:
        return False
        
    st.session_state.last_request_time = current_time
    return True

def validate_message(content: str) -> bool:
    """Validate message content."""
    if not content or len(content.strip()) == 0:
        return False
    if len(content) > 4096:  # Example limit
        return False
    return True
