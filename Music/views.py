from rest_framework.decorators import api_view
from rest_framework.views import APIView

from django.http import JsonResponse

from utils.auth import authUserFunc, authUserClass
from utils.functions import SpotifyApi, formatSongDuration

from Auth.models import UserData


class SongTracks(APIView):
    
    @authUserClass
    def get(self, request, type):
        userId = request.userData["userId"]
        user = UserData.objects.get(userId = userId)
        url = f"me/{type}?limit=20"
        response = SpotifyApi(user, url)
        result = [
            {
                "id": data["album"]["id"],
                "name": data["album"]["name"],
                "releasedOn": data["album"]["release_date"],
                "link": data["album"]["external_urls"]["spotify"],
                "artist": [artist["name"] for artist in data["album"]["artists"]],
                "image": data["album"]["images"][0]["url"],
                "songs": [
                    {
                        "id": song["id"],
                        "name": song["name"],
                        "artists": [artist["name"] for artist in song["artists"]],
                        "play": song["uri"],
                        "url": song["external_urls"]["spotify"],
                        "duration": song["duration_ms"]
                    } for song in data["album"]["tracks"]["items"]
                ]
            } for data in response["items"]
        ]
        return JsonResponse({
            "Status": "Success",
            "Data": result
        })
    
    @authUserClass
    def post(self, request):
        user = UserData.objects.get(userId = request.userData["userId"])
        searchTerm = request.data["searchTerm"]
        limit = request.data.get("songLimit", 15)
        url = f"search?q={searchTerm}&type=track&limit={limit}"
        response = SpotifyApi(user, url)
        result = [
            {
                "id": data["id"],
                "title": data["name"],
                "link": data["external_urls"]["spotify"],
                "play": data["uri"],
                "artists": [
                    {
                        "artistId": artist["id"],
                        "artistName": artist["name"],
                        "link": artist["external_urls"]["spotify"]
                    } for artist in data["artists"]
                ],
                "album": {
                    "albumId": data["album"]["id"],
                    "albumName": data["album"]["name"],
                    "link": data["album"]["external_urls"]["spotify"],
                    "image": data["album"]["images"]
                },
                "duration": data["duration_ms"],
                "preview": data["preview_url"]
            } for data in response["tracks"]["items"]
        ]
        return JsonResponse({
            "Status": "Success",
            "data": result
        })

class HandleSong(APIView):
    
    @authUserClass
    def post(self, request):
        
        userId = request.userData["userId"]
        user = UserData.objects.get(userId = userId)
        
        type = request.data.get("type")
        deviceId = user.device_id or request.data.get("deviceId")
        url = f"me/player/{type}?device_id={deviceId}"
        
        trackUrl = request.data.get("trackUrl")
        body = {"uris": [trackUrl]} if type == 'play' else None
        
        response = SpotifyApi(user, url, "POST" if type == 'play' or type == 'pause' else 'PUT', body)
        return response