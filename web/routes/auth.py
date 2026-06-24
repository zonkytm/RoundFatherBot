import hashlib
import hmac
import json
import time
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from bot.config import settings

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)


def verify_telegram_init_data(init_data: str) -> dict | None:
    try:
        parts = dict(item.split("=", 1) for item in init_data.split("&"))
        hash_val = parts.pop("hash", None)
        if not hash_val:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parts.items()))

        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if computed_hash != hash_val:
            return None

        auth_date = int(parts.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            return None

        user_data = json.loads(unquote(parts.get("user", "{}")))
        return user_data
    except Exception:
        return None


def verify_static_token(token: str) -> bool:
    if not settings.DASHBOARD_TOKEN:
        return False
    return hmac.compare_digest(token, settings.DASHBOARD_TOKEN)


class TokenRequest(BaseModel):
    token: str


@router.post("/auth/verify")
async def verify_token(data: TokenRequest):
    if verify_static_token(data.token):
        return {"status": "ok", "role": "admin"}
    raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    if credentials and verify_static_token(credentials.credentials):
        return {"role": "admin", "source": "token"}

    token_cookie = request.cookies.get("dashboard_token")
    if token_cookie and verify_static_token(token_cookie):
        return {"role": "admin", "source": "cookie"}

    init_data = request.headers.get("X-Telegram-Init-Data")
    if init_data:
        user = verify_telegram_init_data(init_data)
        if user:
            return {"role": "user", "telegram_id": user.get("id"), "data": user}

    return None


async def require_admin(user: dict | None = Depends(get_current_user)) -> dict:
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Admin access required")
    return user


async def require_auth(user: dict | None = Depends(get_current_user)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
