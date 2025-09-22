import os
import requests

from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.http import HttpResponseRedirect, JsonResponse

from utils.auth import authUserClass, authUserFunc
from utils.handleToken import verifyToken, generateToken
from .models import UserData


ACCESS_TOKEN = settings.ACCESS_TOKEN
REFRESH_TOKEN = settings.REFRESH_TOKEN
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET_ID = settings.CLIENT_SECRET_ID
REDIRECT_URI = settings.REDIRECT_URI

SCOPES = "streaming user-read-email user-read-private user-library-read user-library-modify user-read-playback-state user-modify-playback-state"


class Authentication(APIView):
    
    @authUserClass
    def get(self, request):
        userData = request.userData
        return JsonResponse({ 
            "Status": "Logged In", 
            "DisplayName": userData["displayName"],
            "Premium": userData["premium"]
        })
    
    def post(self, request):
        access = request.COOKIES.get(ACCESS_TOKEN)
        refresh = request.COOKIES.get(REFRESH_TOKEN)

        refresh_data = verifyToken(refresh)
        if refresh_data and refresh_data not in ("Token TimeOut", 'Invalid Token'):

            userIdFromToken = refresh_data["userId"]
            user = UserData.objects.get(userId = userIdFromToken)
            new_access_token, new_refresh_token = generateToken(user)

            response = JsonResponse({"Status": "Token Refreshed"})
            response.set_cookie(
                ACCESS_TOKEN, new_access_token, 
                httponly=True, 
                samesite="None", 
                secure=True,
                max_age=60 * 60
            )
            response.set_cookie(
                REFRESH_TOKEN, new_refresh_token, 
                httponly=True, 
                samesite="None", 
                secure=True,
                max_age=60 * 60 * 24 * 7
            )

            return response


@api_view(['GET'])
def CallBack(request):
    code = request.GET.get("code")

    getTokens = "https://accounts.spotify.com/api/token"
    response = requests.post(
        getTokens,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET_ID,
        },
    )
    reponseTokens = response.json()
    
    getUserData = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {reponseTokens['access_token']}"
    }
    userDataResponse = requests.get(getUserData, headers=headers)
    print('Res -', userDataResponse)
    print("403 Status:", userDataResponse.status_code)
    print("403 Headers:", userDataResponse.headers)
    print("403 Body:", userDataResponse.text)

    userData = userDataResponse.json()
    
    getUserId, created = UserData.objects.update_or_create(
        userId = userData["id"],
        defaults={
            "displayName": userData["display_name"],
            "email": userData["email"],
            "premium": True if userData["product"] == 'premium' else False,
            "token": reponseTokens["access_token"],
            "refresh": reponseTokens["refresh_token"],
            "timeOut": reponseTokens["expires_in"]
        }
    )
    
    user = UserData.objects.get(userId = getUserId)
    access_token, refresh_token = generateToken(user)
    
    response = HttpResponseRedirect("http://127.0.0.1:5173/search")
    response.set_cookie(
        ACCESS_TOKEN, access_token, 
        httponly=True, 
        samesite="None", 
        secure=True, 
        max_age=60 * 60
    )
    response.set_cookie(
        REFRESH_TOKEN, refresh_token, 
        httponly=True, 
        samesite="None", 
        secure=True,
        max_age=60 * 60 * 24 * 7
    )
    
    return response


class PremiumPlaySetup(APIView):
    
    @authUserClass
    def get(self, request):
        userId = request.userData["userId"]
        if not userId:
            return JsonResponse({
                "Status": "Failed"
            })
        user = UserData.objects.get(userId = userId)
        token = user.token
        return JsonResponse({
            "Status": "Success",
            "Data": token
        })
        
    @authUserClass
    def post(self, request):
        userId = request.userData["userId"]
        deviceId = request.data.get("deviceId")
        if not deviceId:
            return JsonResponse({
                "Status": "Error",
                "Message": "No Data Found"
            })
        user = UserData.objects.get(userId = userId)
        user.device_id = deviceId
        user.save(update_fields=["device_id"])
        return JsonResponse({
            "Status": "Success"
        })
        