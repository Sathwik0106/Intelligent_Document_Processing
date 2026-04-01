import hashlib
from pathlib import Path

from app.config import settings


def get_uploaded_file_hash(uploaded_file) -> str:
    file_bytes = uploaded_file.getvalue()
    return hashlib.sha256(file_bytes).hexdigest()


def _write_temp_file(file_bytes: bytes, file_name: str) -> str:
    suffix = Path(file_name).suffix.lower() or ".bin"
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    temp_dir = settings.TEMP_UPLOAD_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{file_hash}{suffix}"
    if not temp_path.exists():
        temp_path.write_bytes(file_bytes)
    return str(temp_path)
