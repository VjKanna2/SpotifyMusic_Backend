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
FE_BASE = settings.FE_BASE
BE_BASE = settings.BE_BASE

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
            user.token = new_access_token
            user.refresh = new_refresh_token
            user.save()

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
    tokenResponse = requests.post(
        getTokens,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{BE_BASE}/auth/callback",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET_ID,
        },
    )
    reponseTokens = tokenResponse.json()

    getUserData = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {reponseTokens['access_token']}"
    }
    userDataResponse = requests.get(getUserData, headers=headers)

    if userDataResponse.status_code != 200:
        return HttpResponseRedirect(f"{FE_BASE}/404")

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
    
    response = HttpResponseRedirect(FE_BASE)

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


@api_view(['POST'])
@authUserFunc
def UserLogOut(request):
    user = request.userData['userId']
    deleteUser = UserData.objects.get(userId = user)
    deleteUser.delete()
    response = JsonResponse({
        "Status": "Logged Out Successfully",
        "Message": "Data Cleared"
    })
    response.delete_cookie(ACCESS_TOKEN, path="/", samesite="None")
    response.delete_cookie(REFRESH_TOKEN, path="/", samesite="None")

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
        