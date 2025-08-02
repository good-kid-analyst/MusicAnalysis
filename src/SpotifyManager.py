import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
from configparser import ConfigParser


class SpotifyManager:
    def __init__(self):
        c = ConfigParser()
        c.read("config/config.ini")
        client_credentials_manager = SpotifyClientCredentials(
            client_id=c["SPOTIFY"]["CLIENT_ID"],
            client_secret=c["SPOTIFY"]["CLIENT_SECRET"]
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    @staticmethod
    def get_mock_album():
        """Fallback mock data for testing"""
        mock_albums = [
            {
                'id': 'mock1',
                'name': 'Abbey Road',
                'artist': 'The Beatles',
                'release_date': '1969-09-26',
                'year': '1969',
                'genres': ['rock', 'pop rock', 'psychedelic rock'],
                'genre': 'Rock',
                'image_url': None,
                'total_tracks': 17,
                'popularity': 85
            },
            {
                'id': 'mock2',
                'name': 'Dark Side of the Moon',
                'artist': 'Pink Floyd',
                'release_date': '1973-03-01',
                'year': '1973',
                'genres': ['progressive rock', 'psychedelic rock', 'art rock'],
                'genre': 'Progressive Rock',
                'image_url': None,
                'total_tracks': 10,
                'popularity': 90
            },
            {
                'id': 'mock3',
                'name': 'Thriller',
                'artist': 'Michael Jackson',
                'release_date': '1982-11-30',
                'year': '1982',
                'genres': ['pop', 'rock', 'funk'],
                'genre': 'Pop',
                'image_url': None,
                'total_tracks': 9,
                'popularity': 95
            },
            {
                'id': 'mock4',
                'name': 'Nevermind',
                'artist': 'Nirvana',
                'release_date': '1991-09-24',
                'year': '1991',
                'genres': ['grunge', 'alternative rock', 'punk'],
                'genre': 'Grunge',
                'image_url': None,
                'total_tracks': 12,
                'popularity': 88
            }
        ]

        return random.choice(mock_albums)

    def get_random_album(self):
        """Get a random album from Spotify with detailed information"""
        # if not self.sp:
        #     return self.get_mock_album()
        search_queries = [
            # 'year:1960-1969 genre:rock',
            # 'year:1970-1979 genre:rock',
            # 'year:1980-1989 genre:pop',
            # 'year:1990-1999 genre:alternative',
            # 'year:2000-2009 genre:indie',
            # 'year:2010-2019 genre:electronic',
            # 'year:2020-2024 genre:pop',
            'genre:hip-hop',
            'genre:jazz',
            'genre:r&b',
            'genre:country',
            'genre:metal'
        ]

        query = random.choice(search_queries)
        offset = random.randint(0, 500)

        results = self.sp.search(q=query, type='album', limit=50, offset=offset, market='US')

        if results['albums']['items']:
            album = random.choice(results['albums']['items'])

            # Get detailed album info
            album_details = self.sp.album(album['id'])

            # Get artist genres
            genres = album_details.get('genres', [])
            if not genres and album_details['artists']:
                artist_info = self.sp.artist(album_details['artists'][0]['id'])
                genres = artist_info.get('genres', [])

            return {
                'id': album['id'],
                'name': album['name'],
                'artist': album['artists'][0]['name'] if album['artists'] else 'Unknown',
                'release_date': album.get('release_date', ''),
                'year': album.get('release_date', '')[:4] if album.get('release_date') else '',
                'genres': genres[:3],  # Limit to top 3 genres
                'genre': genres[0] if genres else 'Various',
                'image_url': album['images'][0]['url'] if album['images'] else None,
                'total_tracks': album.get('total_tracks', 0),
                'popularity': album.get('popularity', 0)
            }

    def search_albums(self, query, limit=10):
        """Search for albums on Spotify"""
        if not self.sp:
            return self.get_mock_search_results(query)

        try:
            results = self.sp.search(q=query, type='album', limit=limit, market='US')
            albums = []

            for album in results['albums']['items']:
                # Get genres from artist
                genres = []
                if album['artists']:
                    try:
                        artist_info = self.sp.artist(album['artists'][0]['id'])
                        genres = artist_info.get('genres', [])
                    except:
                        pass

                albums.append({
                    'id': album['id'],
                    'name': album['name'],
                    'artist': album['artists'][0]['name'] if album['artists'] else 'Unknown',
                    'year': album.get('release_date', '')[:4] if album.get('release_date') else '',
                    'genres': genres[:3],
                    'genre': genres[0] if genres else 'Various',
                    'total_tracks': album.get('total_tracks', 0),
                    'image_url': album['images'][0]['url'] if album['images'] else None
                })

            return albums

        except Exception as e:
            print(f"Error searching albums: {e}")
            return self.get_mock_search_results(query)

    @staticmethod
    def get_mock_search_results(query):
        """Mock search results for testing"""
        all_albums = [
            {'id': 'mock1', 'name': 'Abbey Road', 'artist': 'The Beatles', 'year': '1969', 'genres': ['rock'],
             'genre': 'Rock', 'total_tracks': 17},
            {'id': 'mock2', 'name': 'Dark Side of the Moon', 'artist': 'Pink Floyd', 'year': '1973',
             'genres': ['progressive rock'], 'genre': 'Progressive Rock', 'total_tracks': 10},
            {'id': 'mock3', 'name': 'Thriller', 'artist': 'Michael Jackson', 'year': '1982', 'genres': ['pop'],
             'genre': 'Pop', 'total_tracks': 9},
            {'id': 'mock4', 'name': 'Nevermind', 'artist': 'Nirvana', 'year': '1991', 'genres': ['grunge'],
             'genre': 'Grunge', 'total_tracks': 12},
            {'id': 'mock5', 'name': 'OK Computer', 'artist': 'Radiohead', 'year': '1997',
             'genres': ['alternative rock'],
             'genre': 'Alternative Rock', 'total_tracks': 12},
            {'id': 'mock6', 'name': 'Kind of Blue', 'artist': 'Miles Davis', 'year': '1959', 'genres': ['jazz'],
             'genre': 'Jazz', 'total_tracks': 5},
            {'id': 'mock7', 'name': 'Pet Sounds', 'artist': 'The Beach Boys', 'year': '1966', 'genres': ['pop'],
             'genre': 'Pop', 'total_tracks': 13},
            {'id': 'mock8', 'name': 'The Velvet Underground & Nico', 'artist': 'The Velvet Underground', 'year': '1967',
             'genres': ['art rock'], 'genre': 'Art Rock', 'total_tracks': 11}
        ]

        # Simple text matching for mock data
        query_lower = query.lower()
        matching_albums = [
            album for album in all_albums
            if (query_lower in album['name'].lower() or
                query_lower in album['artist'].lower())
        ]

        return matching_albums[:8]
