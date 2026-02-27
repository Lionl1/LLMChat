"""HTTP client for OpenAI-compatible chat completions."""

from typing import Any, Dict, List, Optional

import requests

def request_chat_completion(
    api_url: str,
    api_key: Optional[str],
    model: str,
    messages: List[Dict[str, str]],
    params: Dict[str, Any],
    timeout: int,
) -> Dict[str, Any]:
    """Send a chat completion request and return the raw response."""
    if not api_url:
        raise ValueError("API URL is required.")
    if not model:
        raise ValueError("Model name is required.")

    data = {
        "model": model,
        "messages": messages,
        "temperature": params.get("temperature"),
        "max_tokens": params.get("max_tokens"),
        "top_p": params.get("top_p"),
        "stream": False,
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        sanitized = api_key.strip()
        if sanitized.lower().startswith("bearer "):
            headers["Authorization"] = sanitized
        else:
            headers["Authorization"] = f"Bearer {sanitized}"

    response = requests.post(api_url, json=data, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()
