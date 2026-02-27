"""FastAPI backend for the chat UI."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests

from .config.app_config import AppConfig
from .utils.extract_text_client import extract_text_from_file
from .utils.llm_client import request_chat_completion

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="Local LLM Chat")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

class ChatParams(BaseModel):
    temperature: float = Field(AppConfig.DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(AppConfig.DEFAULT_MAX_TOKENS, ge=1)
    top_p: float = Field(AppConfig.DEFAULT_TOP_P, ge=0.0, le=1.0)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    api_url: str = AppConfig.API_URL
    api_key: Optional[str] = None
    model: str = AppConfig.DEFAULT_MODEL
    params: ChatParams = ChatParams()

class ChatResponse(BaseModel):
    message: str

@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/api/config")
def config() -> Dict[str, Any]:
    return {
        "api_url": AppConfig.API_URL,
        "model": AppConfig.DEFAULT_MODEL,
        "extract_api_url": AppConfig.EXTRACT_TEXT_API_URL,
        "system_message": AppConfig.DEFAULT_SYSTEM_MESSAGE.get("en", ""),
        "params": {
            "temperature": AppConfig.DEFAULT_TEMPERATURE,
            "max_tokens": AppConfig.DEFAULT_MAX_TOKENS,
            "top_p": AppConfig.DEFAULT_TOP_P,
        },
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    api_key = request.api_key or os.getenv(AppConfig.API_KEY_ENV_VAR, "")
    try:
        response = request_chat_completion(
            api_url=request.api_url,
            api_key=api_key,
            model=request.model,
            messages=request.messages,
            params=request.params.model_dump(),
            timeout=AppConfig.TIMEOUT,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    message = ""
    choices = response.get("choices") or []
    if choices:
        first = choices[0] or {}
        if isinstance(first, dict):
            msg = first.get("message")
            if isinstance(msg, dict) and "content" in msg:
                message = str(msg["content"]).strip()
            elif "text" in first:
                message = str(first["text"]).strip()

    if not message:
        raise HTTPException(status_code=502, detail="Empty response from model.")

    return ChatResponse(message=message)

@app.post("/api/extract")
async def extract(
    files: List[UploadFile] = File(...),
    extract_api_url: Optional[str] = Form(None),
) -> Dict[str, Any]:
    api_url = extract_api_url or AppConfig.EXTRACT_TEXT_API_URL
    if not api_url:
        raise HTTPException(status_code=400, detail="Extract-text API URL is required.")

    results: List[Dict[str, Any]] = []
    for upload in files:
        content = await upload.read()
        if not content:
            continue
        try:
            extracted_files = extract_text_from_file(
                content,
                upload.filename or "file",
                api_url,
                AppConfig.EXTRACT_TEXT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"extract-text is unreachable: {exc}",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        results.extend(extracted_files)

    text_parts = []
    for item in results:
        name = item.get("path") or item.get("filename") or "file"
        text = (item.get("text") or "").strip()
        if not text:
            continue
        text_parts.append(f"File: {name}\n{text}")

    combined = "\n\n".join(text_parts)
    if AppConfig.MAX_IMPORTED_CHARS and len(combined) > AppConfig.MAX_IMPORTED_CHARS:
        combined = combined[: AppConfig.MAX_IMPORTED_CHARS].rstrip() + "\n\n[truncated]"

    return {"files": results, "text": combined}
