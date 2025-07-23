import datetime
import pprint

import spotipy
from configparser import ConfigParser
from spotipy.oauth2 import SpotifyOAuth
import polars as pl


class SpotifyAnalysis:
    def __init__(self):
        c = ConfigParser()
        c.read("config/config.ini")
        self.client_id = c["SPOTIFY"]["CLIENT_ID"]
        self.client_secret = c["SPOTIFY"]["CLIENT_SECRET"]
        self.scope = c["SPOTIFY"]["SCOPE"]
        self.redirect = c["SPOTIFY"]["REDIRECT_URI"]

    def run(self):
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect,
            scope=self.scope)
        )
        results = sp.current_user_recently_played(limit=50,
                                                  before=int(datetime.datetime(2025, 7, 22).timestamp() * 1000))
        for result in results["items"]:
            print(result["track"]["name"], result["played_at"])
            # results = (pl
        #            .from_dicts(results)
        #            .select("items")
        #            .unnest("items")
        #            .select("album")
        #            .unnest("album")
        #            )
        # print(results)


if __name__ == '__main__':
    SpotifyAnalysis().run()