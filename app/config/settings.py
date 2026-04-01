import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=True)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-flash-lite-latest").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2").strip()
CHUNK_MAX_CHARACTERS = _get_int("CHUNK_MAX_CHARACTERS", 3000)
CHUNK_NEW_AFTER_N_CHARS = _get_int("CHUNK_NEW_AFTER_N_CHARS", 2400)
CHUNK_COMBINE_TEXT_UNDER_N_CHARS = _get_int("CHUNK_COMBINE_TEXT_UNDER_N_CHARS", 500)
RAG_RETRIEVAL_K = _get_int("RAG_RETRIEVAL_K", 3)
MAX_UPLOAD_SIZE_MB = _get_int("MAX_UPLOAD_SIZE_MB", 20)
TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", BASE_DIR / ".cache" / "uploads"))
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", BASE_DIR / ".cache" / "vector_store"))
SUPPORTED_EXTENSIONS = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".docx",
    ".ppt",
    ".pptx",
)
SUPPORTED_UPLOAD_TYPES = tuple(ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS)


def refresh_env():
    load_dotenv(ENV_PATH, override=True)


def get_gemini_api_key() -> str:
    refresh_env()
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def get_tesseract_cmd() -> str:
    explicit = (os.getenv("TESSERACT_CMD") or "").strip()
    if explicit:
        return explicit

    discovered = shutil.which("tesseract")
    if discovered:
        return discovered

    candidates = [
        Path(r"C:\Users\sathw\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""
