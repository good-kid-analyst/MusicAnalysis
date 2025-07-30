import datetime
import pprint

import spotipy
from configparser import ConfigParser
from spotipy.oauth2 import SpotifyOAuth
import polars as pl
import random


class SpotifyAnalysis:
    def __init__(self):
        c = ConfigParser()
        c.read("config/config.ini")
        self.client_id = c["SPOTIFY"]["CLIENT_ID"]
        self.client_secret = c["SPOTIFY"]["CLIENT_SECRET"]
        self.scope = c["SPOTIFY"]["SCOPE"]
        self.redirect = c["SPOTIFY"]["REDIRECT_URI"]

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect,
            scope=self.scope)
        )

    def run(self):
        results = self.sp.current_user_recently_played(limit=50,
                                                  before=int(datetime.datetime(2025, 7, 22).timestamp() * 1000))
        for result in results["items"]:
            print(result["track"]["name"], result["played_at"])

    def get_user(self, username):
        user = self.sp.user(username)
        playlists = self.sp.user_playlists(username)
        tracks = []
        for playlist in playlists["items"]:
            playlist_info = self.sp.playlist(playlist["id"])
            for track in playlist_info["tracks"]["items"]:
                tracks.append(track["track"]["id"])
                if len(tracks) > 10:
                    break

    def random_track(self, q=None):
        if q is None:
            q = "rap year:2025"
        albums = self.sp.search(q=q, type='album', limit=50)['albums']['items']
        album = random.choice([album for album in albums if album["total_tracks"] > 10])
        top_tracks = self.sp.album_tracks(album['id'])
        track = random.choice(top_tracks["items"])
        artists = [a["name"] for a in track["artists"]]
        name = track["name"]
        album_name = album["name"]
        release_date = album["release_date"]
        tracks = album["total_tracks"]
        cover = album["images"][-1]["url"]
        album_obj = {
            "name": album_name,
            "artists": artists,
            "track": name,
            "release_date": release_date,
            "cover": cover,
            "total_tracks": tracks,
        }
        return album_obj

    def get_all_recent_tracks(self, start_date: datetime.datetime, end_date: datetime.datetime):
        """Retrieve all tracks between two dates"""
        all_tracks = []
        after = int(start_date.timestamp() * 1000)
        before = int(end_date.timestamp() * 1000)

        while True:
            results = self.sp.current_user_recently_played(limit=50, after=after)
            if not results['items']:
                break
            # Filter items within our date range
            filtered = [item for item in results['items']
                        if start_date <= datetime.datetime.strptime(item['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ") <= end_date]
            print(filtered[-1]["played_at"])
            all_tracks.extend(filtered)

            # Set new 'after' to the oldest track's timestamp
            oldest = min(item['played_at'] for item in results['items'])
            after = int(datetime.datetime.strptime(oldest, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000 + 86400000)  # Add 1 day in ms
            if after > before:
                break

        return all_tracks


if __name__ == '__main__':
    SpotifyAnalysis().random_track()