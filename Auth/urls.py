from django.urls import path
from .views import Authentication, CallBack, PremiumPlaySetup, UserLogOut

urlpatterns = [
    path('token', Authentication.as_view()),
    path('callback', CallBack),
    path('premiumFeature', PremiumPlaySetup.as_view()),
    path('logout', UserLogOut)
]
