import json
import os
import secrets
from datetime import datetime
from typing import Any, Iterable, List, Optional

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash


def now_utc() -> datetime:
    return datetime.utcnow()


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(text: Optional[str], default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def ensure_list_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


def new_storage_name(original_name: str) -> str:
    _, ext = os.path.splitext(original_name)
    token = secrets.token_hex(16)
    return f"{token}{ext}".lower()


def storage_path(storage_name: str) -> str:
    return os.path.join(current_app.config["STORAGE_DIR"], storage_name)
