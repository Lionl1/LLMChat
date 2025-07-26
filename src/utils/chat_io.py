"""Chat import/export module."""

import json
import streamlit as st
from typing import Optional

def export_chat(chat_name: str) -> Optional[str]:
    """Export selected chat to file."""
    try:
        if chat_name and chat_name in st.session_state.chats:
            chat_data = st.session_state.chats[chat_name]
            safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{safe_name}_export.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
            return filename
    except Exception as e:
        st.error(f"Error exporting chat: {str(e)}")
    return None

def import_chat(uploaded_file) -> None:
    """Import chat from file."""
    lang = st.session_state.language
    try:
        chat_data = json.load(uploaded_file)
        chat_name = f"Import: {uploaded_file.name}"
        
        if not isinstance(chat_data, list) or not all("role" in msg and "content" in msg for msg in chat_data):
            raise ValueError("Invalid chat format")
        
        st.session_state.chats[chat_name] = chat_data
        st.session_state.current_chat = chat_name
        st.session_state.messages = chat_data
        from utils.chat_manager import save_chats
        save_chats()
    except Exception as e:
        st.error(f"Import error: {str(e)}")
