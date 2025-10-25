import requests
from django.http import JsonResponse
from django.core.cache import cache
from Auth.models import UserData
from .handleToken import refreshToken

def SpotifyApi(user: UserData, endpoint, method="GET", params=None):
    
    if method == 'GET':
        cacheKey = f"spotify-user-{user.userId}-{endpoint}-{params}"
        cacheResponse = cache.get(cacheKey)
        if cacheResponse:
            return cacheResponse
    
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {user.token}"}

    if method == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method == 'PUT':
        response = requests.put(url, headers=headers, json=params)
    else:
        response = requests.post(url, headers=headers, json=params)

    if response.status_code == 401:
        new_token = refreshToken(user.refresh)
        if not new_token:
            return JsonResponse({ 
                "Status": "Token Expired",
                "Message": "Login Again"
            })
        user.token = new_token
        user.save()
        headers = {"Authorization": f"Bearer {new_token}"}
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=params)
        else:
            response = requests.post(url, headers=headers, json=params)
    
    if response.status_code == 204:
        data = {"Status": "Success", "Message": "No Message"}
    else:
        try: 
            data = response.json()
        except ValueError:
            data = {"Status": "Success", "Message": "Value Error"}
    
    if method == 'GET':
        cache.set(cacheKey, data, timeout=60)

    return data

def formatSongDuration(milliSecond):
    total_seconds = milliSecond // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02}"
