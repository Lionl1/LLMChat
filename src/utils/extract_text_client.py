"""Client for the extract-text API."""

from typing import Any, Dict, List

import requests

def extract_text_from_file(
    file_bytes: bytes,
    filename: str,
    api_base_url: str,
    timeout: int,
) -> List[Dict[str, Any]]:
    """Send a file to the extract-text API and return extracted file data."""
    if not api_base_url:
        raise ValueError("Extract-text API URL is not configured.")

    api_url = api_base_url.rstrip("/") + "/v1/extract/file"
    files = {"file": (filename, file_bytes)}

    response = requests.post(api_url, files=files, timeout=timeout)
    response.raise_for_status()

    payload = response.json()
    if payload.get("status") != "success":
        message = payload.get("message", "Extract-text API error.")
        raise ValueError(message)

    return payload.get("files", [])
