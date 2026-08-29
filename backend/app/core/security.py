from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iteration_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_text)
        salt = _b64url_decode(salt_text)
        expected = _b64url_decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    settings = get_settings()
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int((datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
    payload = {"sub": str(subject), "exp": exp}
    signing_input = f"{_b64url(json.dumps(header,separators=(',',':')).encode())}.{_b64url(json.dumps(payload,separators=(',',':')).encode())}"
    signature = hmac.new(settings.secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def decode_access_token(token: str) -> str | None:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(get_settings().secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        actual = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected, actual):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) <= int(datetime.now(timezone.utc).timestamp()):
            return None
        subject = payload.get("sub")
        return str(subject) if subject is not None else None
    except Exception:
        return None
