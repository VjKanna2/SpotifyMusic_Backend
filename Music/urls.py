from django.urls import path
from .views import SongTracks, HandleSong

urlpatterns = [
    path('search', SongTracks.as_view()),
    path('handleSong', HandleSong.as_view()),
    path('get/<str:type>', SongTracks.as_view()),
]
