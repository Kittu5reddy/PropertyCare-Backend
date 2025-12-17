import secrets
import httpx
from fastapi import APIRouter, HTTPException
from config import settings


STATE_TTL = 300  # seconds


def build_authorize_url(state: str) -> str:
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "consent",
    }
    # Manual query building (avoid external libs for now)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}?{query}"




async def exchange_code_for_tokens(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")
        return resp.json()


async def fetch_userinfo(access_token: str):
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(userinfo_url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"UserInfo fetch failed: {resp.text}")
        return resp.json()
