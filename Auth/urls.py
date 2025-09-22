from django.urls import path
from .views import Authentication, CallBack, PremiumPlaySetup

urlpatterns = [
    path('token', Authentication.as_view()),
    path('callback', CallBack),
    path('premiumFeature', PremiumPlaySetup.as_view()),
]
