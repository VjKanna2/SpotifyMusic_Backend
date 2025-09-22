from django.db import models
from django.utils import timezone
from datetime import timedelta

class UserData(models.Model):
    
    userId = models.CharField(max_length=100, unique=True)
    displayName = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    premium = models.BooleanField(default=False)
    token = models.CharField(max_length=300)
    refresh = models.CharField(max_length=300)
    timeOut = models.IntegerField()
    updatedOn = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=100, null=True)
    
    def __str__(self):
        return self.userId
    
    def isTokenExpired(self):
        tokenTime = self.updatedOn + timedelta(seconds=self.timeOut)
        return timezone.now() >= tokenTime
