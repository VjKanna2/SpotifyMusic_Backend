from django.conf import settings
from django.http import JsonResponse
from .handleToken import verifyToken
from functools import wraps

ACCESS_TOKEN = settings.ACCESS_TOKEN
REFRESH_TOKEN = settings.REFRESH_TOKEN

def isUserAuthenticated(request):
    
    access = request.COOKIES.get(ACCESS_TOKEN)
    refresh = request.COOKIES.get(REFRESH_TOKEN)
    
    if not access and not refresh:
        return None, JsonResponse({ "Status": "Not Logged In" })
    
    access_token_data = verifyToken(access)
    if access_token_data and access_token_data not in ('Token TimeOut', "Invalid Token"):
        return {
            "userId": access_token_data["userId"], 
            "displayName": access_token_data["displayName"],
            "premium": access_token_data["premium"]
        }, None
    
    refresh_token_data = verifyToken(refresh)
    if refresh_token_data and refresh_token_data not in ('Token TimeOut', "Invalid Token"):
        return None, JsonResponse({
            "Status": "Token Expired",
            "Message": "Access Token Expired"
        })
    else:
        response = JsonResponse({ 
            "Status": "Token Expired",
            "Message": "Login Again"
        })
        response.delete_cookie(ACCESS_TOKEN)
        response.delete_cookie(REFRESH_TOKEN)
        return None, response

def authUserClass(viewFunc):
    @wraps(viewFunc)
    def wrapper(self, request, *args, **kwargs):
        userData, response = isUserAuthenticated(request)
        if response:
            return response
        request.userData = userData
        return viewFunc(self, request, *args, **kwargs)
    return wrapper

def authUserFunc(viewFunc):
    @wraps(viewFunc)
    def wrapper(request, *args, **kwargs):
        userData, response = isUserAuthenticated(request)
        if response:
            return response
        request.userData = userData
        return viewFunc(request, *args[1:], **kwargs)
    return wrapper