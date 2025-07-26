"""
Main application module for AI Chat Assistant.

This module implements a Streamlit-based chat interface with features like:
- Multiple chat management
- Model parameter configuration
- Chat export/import
- Multilingual support (English/Russian)
"""

import streamlit as st
from dotenv import load_dotenv

from config.app_config import AppConfig
from utils.chat_manager import (
    load_saved_chats, save_chats, create_new_chat,
    switch_chat, delete_chat, clear_current_chat
)
from utils.chat_io import export_chat, import_chat
from utils.message_handler import (
    trim_message_history, get_model_response,
    rate_limit_check, validate_message
)

# Load environment variables
load_dotenv()

def init_session_state() -> None:
    """Initialize session state variables."""
    defaults = {
        "language": "en",
        "current_chat": "Default",
        "chats": load_saved_chats(),
        "is_chat_input_disabled": False,
        "pending_prompt": None,
        "model_params": {
            "temperature": AppConfig.DEFAULT_TEMPERATURE,
            "max_tokens": AppConfig.DEFAULT_MAX_TOKENS,
            "top_p": AppConfig.DEFAULT_TOP_P,
            "top_k": AppConfig.DEFAULT_TOP_K,
            "repetition_penalty": AppConfig.DEFAULT_REPETITION_PENALTY
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    if "messages" not in st.session_state:
        lang = st.session_state.language
        st.session_state.messages = [
            {"role": "system", "content": AppConfig.DEFAULT_SYSTEM_MESSAGE[lang]}
        ]
        st.session_state.chats[st.session_state.current_chat] = st.session_state.messages

def render_sidebar() -> None:
    """Render sidebar with settings and controls."""
    with st.sidebar:
        lang = st.session_state.language
        st.markdown("""
            <style>
            [data-testid=stSidebar] {
                background-color: #252526;
                border-right: 1px solid #454545;
            }
            [data-testid=stSidebar] .stMarkdown {
                color: #D4D4D4;
            }
            .sidebar-header {
                color: #4CAF50;
                font-size: 1.2em;
                margin-bottom: 1em;
            }
            .settings-section {
                background-color: #2D2D2D;
                padding: 1em;
                border-radius: 4px;
                margin-bottom: 1em;
                border: 1px solid #454545;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Language settings
        with st.expander("🌍 Язык / Language", expanded=True):
            selected_lang = st.selectbox(
                "Language selector",
                ["ru", "en"],
                index=0 if lang == "ru" else 1,
                key="language_selector",
                label_visibility="collapsed"
            )
            if selected_lang != lang:
                st.session_state.language = selected_lang
                st.rerun()
        
        # Chat management
        with st.expander("💬 " + ("Управление чатами" if lang == "ru" else "Chat Management"), expanded=True):
            # New chat button
            if st.button("➕ " + ("Новый чат" if lang == "ru" else "New Chat"),
                        use_container_width=True,
                        type="primary"):
                create_new_chat()
            
            st.divider()
            
            # Chat selection
            current_idx = list(st.session_state.chats.keys()).index(st.session_state.current_chat)
            selected_chat = st.selectbox(
                "📚 " + ("Выбрать чат" if lang == "ru" else "Select Chat"),
                list(st.session_state.chats.keys()),
                index=current_idx
            )
            
            if selected_chat != st.session_state.current_chat:
                switch_chat(selected_chat)
            
            # Chat actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 " + ("Очистить" if lang == "ru" else "Clear"),
                           disabled=selected_chat == "Default",
                           use_container_width=True):
                    clear_current_chat()
            with col2:
                if st.button("❌ " + ("Удалить" if lang == "ru" else "Delete"),
                           disabled=selected_chat == "Default",
                           use_container_width=True,
                           type="secondary"):
                    delete_chat(selected_chat)
        
        # Export/Import
        with st.expander("📁 " + ("Экспорт/Импорт" if lang == "ru" else "Export/Import")):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 " + ("Экспорт" if lang == "ru" else "Export"),
                           disabled=selected_chat == "Default",
                           use_container_width=True):
                    filename = export_chat(selected_chat)
                    if filename:
                        st.success(("Чат экспортирован в " if lang == "ru" else "Chat exported to ") + filename)
            
            with col2:
                uploaded_file = st.file_uploader(
                    "📥 " + ("Импорт" if lang == "ru" else "Import"),
                    type=['json'],
                    label_visibility="collapsed"
                )
                if uploaded_file is not None:
                    import_chat(uploaded_file)
        
        render_model_settings()

def render_model_settings() -> None:
    """Render model parameter settings."""
    lang = st.session_state.language
    params = st.session_state.model_params

    with st.expander("⚙️ " + ("Настройки модели" if lang == "ru" else "Model Settings")):
        # Temperature
        col1, col2 = st.columns([3, 1])
        with col1:
            params["temperature"] = st.slider(
                "🌡️ " + ("Температура" if lang == "ru" else "Temperature"),
                0.0, 1.0, params["temperature"], 0.01,
                help=("Контролирует креативность ответов. Низкие значения делают ответы более предсказуемыми, " +
                    "высокие - более творческими") if lang == "ru" else 
                    "Controls response creativity. Lower values make responses more predictable, higher values more creative"
            )
        with col2:
            st.text_input(
                "Temperature value",
                value=f"{params['temperature']:.2f}",
                disabled=True,
                key="temp_display",
                label_visibility="collapsed"
            )

        # Max tokens
        col1, col2 = st.columns([3, 1])
        with col1:
            params["max_tokens"] = st.slider(
                "📏 " + ("Макс. токенов" if lang == "ru" else "Max Tokens"),
                10, 4096, params["max_tokens"],
                help=("Максимальная длина ответа модели") if lang == "ru" else 
                    "Maximum length of model response"
            )
        with col2:
            st.text_input(
                "Max tokens value",
                value=str(params["max_tokens"]),
                disabled=True,
                key="tokens_display",
                label_visibility="collapsed"
            )

        # Advanced settings
        with st.expander("🔧 " + ("Расширенные настройки" if lang == "ru" else "Advanced Settings")):
            params["top_p"] = st.slider(
                "Top P",
                0.0, 1.0, params["top_p"], 0.01,
                help=("Контролирует разнообразие ответов. Меньшие значения делают ответы более сфокусированными") if lang == "ru"
                    else "Controls response diversity. Lower values make responses more focused"
            )
            params["top_k"] = st.slider(
                "Top K",
                1, 100, params["top_k"],
                help=("Количество токенов для рассмотрения при генерации") if lang == "ru"
                    else "Number of tokens to consider when generating"
            )
            params["repetition_penalty"] = st.slider(
                "🔄 " + ("Штраф за повторения" if lang == "ru" else "Repetition Penalty"),
                1.0, 2.0, params["repetition_penalty"], 0.01,
                help=("Помогает избежать повторений в тексте") if lang == "ru"
                    else "Helps avoid repetitions in text"
            )

def render_chat_messages() -> None:
    """Render chat message history."""
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                content = message["content"].replace("\n", "  \n")
                if message["role"] == "assistant":
                    st.markdown(content, unsafe_allow_html=True)
                else:
                    st.text(content)

def handle_user_input(user_input: str) -> None:
    """Handle user input and get model response."""
    if not validate_message(user_input) or not rate_limit_check():
        return
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.is_chat_input_disabled = True
    
    st.session_state.chats[st.session_state.current_chat] = trim_message_history(
        st.session_state.messages
    )
    save_chats()
    
    lang = st.session_state.language
    with st.spinner(AppConfig.THINKING_TEXT[lang]):
        response = get_model_response(st.session_state.messages)
        
        if response and "choices" in response and response["choices"]:
            assistant_response = response["choices"][0]["text"].strip()
            
            if assistant_response:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": assistant_response
                })
                
                st.session_state.chats[st.session_state.current_chat] = trim_message_history(
                    st.session_state.messages
                )
                save_chats()
    
    st.session_state.is_chat_input_disabled = False
    st.rerun()

def main() -> None:
    """Main application entry point."""
    init_session_state()
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            font-family: 'IBM Plex Mono', monospace;
        }
        .stTextInput > div > div > input {
            background-color: #2D2D2D;
            color: #D4D4D4;
            border: 1px solid #454545;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        .stSelectbox > div > div {
            background-color: #2D2D2D;
            color: #D4D4D4;
            border: 1px solid #454545;
        }
        .stMarkdown code {
            background-color: #2D2D2D;
            padding: 2px 6px;
            border-radius: 4px;
            color: #4CAF50;
        }
        div[data-testid="stToolbar"] {
            background-color: #252526;
            border-bottom: 1px solid #454545;
        }
        </style>
    """, unsafe_allow_html=True)
    
    lang = st.session_state.language
    
    render_sidebar()
    render_chat_messages()
    
    user_input = st.chat_input(
        AppConfig.PLACEHOLDER_TEXT[lang],
        disabled=st.session_state.is_chat_input_disabled
    )
    
    if user_input and not st.session_state.is_chat_input_disabled:
        handle_user_input(user_input)

if __name__ == "__main__":
    main()