"""Chat management module."""

import os
import json
from datetime import datetime
from typing import Dict, List
import streamlit as st

from config.app_config import AppConfig

def load_saved_chats() -> Dict[str, List]:
    """Load saved chats from file with validation."""
    try:
        if os.path.exists(AppConfig.CHATS_FILE):
            with open(AppConfig.CHATS_FILE, 'r', encoding='utf-8') as f:
                chats = json.load(f)
                
                if not isinstance(chats, dict):
                    raise ValueError("Invalid chat file format")
                    
                if len(chats) > AppConfig.MAX_CHATS:
                    oldest = sorted(chats.keys())[:len(chats) - AppConfig.MAX_CHATS]
                    for key in oldest:
                        del chats[key]
                
                return chats
    except Exception as e:
        st.error(f"Error loading chats: {str(e)}")
    return {"Default": []}

def save_chats() -> None:
    """Save chats to file with error handling."""
    try:
        if "chats" in st.session_state:
            with open(AppConfig.CHATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving chats: {str(e)}")

def generate_chat_name() -> str:
    """Generate unique chat name with timestamp."""
    chat_count = len(st.session_state.chats)
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"Chat {chat_count + 1} ({timestamp})"

def create_new_chat(chat_name: str = None) -> None:
    """Create a new chat with automatic naming."""
    if chat_name:
        chat_name = "".join(c for c in chat_name if c.isalnum() or c in " -_()").strip()
        if not chat_name:
            chat_name = generate_chat_name()
    
    if chat_name not in st.session_state.chats:
        lang = st.session_state.language
        st.session_state.chats[chat_name] = [
            {"role": "system", "content": AppConfig.DEFAULT_SYSTEM_MESSAGE[lang]}
        ]
        st.session_state.current_chat = chat_name
        st.session_state.messages = st.session_state.chats[chat_name]
        save_chats()
        st.rerun()

def switch_chat(chat_name: str) -> None:
    """Switch to selected chat."""
    if chat_name in st.session_state.chats:
        st.session_state.current_chat = chat_name
        st.session_state.messages = st.session_state.chats[chat_name]
        st.rerun()

def delete_chat(chat_name: str) -> None:
    """Delete selected chat."""
    if chat_name in st.session_state.chats and chat_name != "Default":
        del st.session_state.chats[chat_name]
        
        if st.session_state.current_chat == chat_name:
            st.session_state.current_chat = "Default"
            st.session_state.messages = st.session_state.chats["Default"]
        
        save_chats()
        st.rerun()

def clear_current_chat() -> None:
    """Clear current chat history while keeping system message."""
    if "messages" in st.session_state and st.session_state.messages:
        system_messages = [msg for msg in st.session_state.messages if msg["role"] == "system"]
        st.session_state.messages = system_messages or [
            {"role": "system", "content": AppConfig.DEFAULT_SYSTEM_MESSAGE[st.session_state.language]}
        ]
        st.session_state.chats[st.session_state.current_chat] = st.session_state.messages
        save_chats()
        st.rerun()
