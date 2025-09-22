import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from Auth.models import UserData
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
TOKEN_SECRET = settings.SECRET_KEY
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET_ID = settings.CLIENT_SECRET_ID


def generateToken(payload):
    access_payload = {
        "userId": payload.userId,
        "displayName": payload.displayName,
        "premium": payload.premium,
        "exp": now + timedelta(hours=1),
        "iat": now,
        "type": "access"
    }
    refresh_payload = {
        "userId": payload.userId,
        "displayName": payload.displayName,
        "premium": payload.premium,
        "exp": now + timedelta(days=1),
        "iat": now,
        "type": "refresh"
    }
    access_token = jwt.encode(access_payload, TOKEN_SECRET, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, TOKEN_SECRET, algorithm="HS256")
    return access_token, refresh_token


def verifyToken(token):
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token TimeOut"
    except jwt.InvalidTokenError:
        return "Invalid Token"


def refreshToken(refresh_token):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET_ID,
    }
    response = requests.post(url, data=data)
    token_data = response.json()
    
    if "access_token" in token_data:
        return token_data["access_token"]
    else:
        return None
