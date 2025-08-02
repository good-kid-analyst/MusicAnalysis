import re
from difflib import SequenceMatcher


class MusicWordleGame:
    def __init__(self,
                 _id,
                 target_album=None,
                 guesses=None,
                 n_guesses=0,
                 max_guesses=6,
                 is_completed=False,
                 is_won=False,
                 created_at=None):
        if guesses is None:
            guesses = []
        self.game_id = _id
        self.target_album = target_album
        self.guesses = guesses
        self.n_guesses = n_guesses
        self.max_guesses = max_guesses
        self.is_completed = is_completed
        self.is_won = is_won
        self.created_at = created_at

        self.genre_keywords = {
            'rock': ['rock', 'metal', 'punk', 'grunge', 'alternative'],
            'pop': ['pop', 'dance', 'electropop', 'synthpop'],
            'electronic': ['electronic', 'techno', 'house', 'edm', 'ambient'],
            'hip-hop': ['hip-hop', 'rap', 'trap', 'r&b'],
            'jazz': ['jazz', 'blues', 'soul', 'funk'],
            'classical': ['classical', 'orchestral', 'symphony'],
            'country': ['country', 'folk', 'bluegrass', 'americana'],
            'indie': ['indie', 'alternative', 'underground']
        }

    def add_guess(self, album_data):
        if len(self.guesses) < self.max_guesses and not self.is_completed:
            self.guesses.append(album_data)
            return True
        return False

    def compare_albums(self, guessed_album):
        """Compare guessed album with target album and return detailed comparison"""
        if not self.target_album:
            return None

        target = self.target_album
        guess = guessed_album

        comparison = {
            'album': self.compare_strings(guess.get('name', ''), target.get('name', '')),
            'artist': self.compare_artists(guess.get('artist', ''), target.get('artist', '')),
            'year': self.compare_years(guess.get('year'), target.get('year')),
            'decade': self.compare_decades(guess.get('year'), target.get('year')),
            'genre': self.compare_genres(guess.get('genres', []), target.get('genres', [])),
            'tracks': self.compare_tracks(guess.get('total_tracks'), target.get('total_tracks'))
        }

        # Check if it's a perfect match
        is_correct = (
                comparison['album']['status'] == 'correct' or
                self.is_album_match(guess.get('name', ''), target.get('name', ''))
        )

        return comparison, is_correct

    def compare_strings(self, guess, target):
        """Compare two strings with exact and partial matching"""
        if not guess or not target:
            return {'status': 'incorrect'}

        guess_clean = self.normalize_string(guess)
        target_clean = self.normalize_string(target)

        if guess_clean == target_clean:
            return {'status': 'correct'}

        # Check for partial matches
        similarity = SequenceMatcher(None, guess_clean, target_clean).ratio()
        if similarity >= 0.8:
            return {'status': 'partial'}

        return {'status': 'incorrect'}

    def compare_artists(self, guess_artist, target_artist):
        """Compare artists with consideration for collaborations"""
        if not guess_artist or not target_artist:
            return {'status': 'incorrect'}

        guess_clean = self.normalize_string(guess_artist)
        target_clean = self.normalize_string(target_artist)

        if guess_clean == target_clean:
            return {'status': 'correct'}

        # Check if one artist is part of the other (collaborations, featuring, etc.)
        if guess_clean in target_clean or target_clean in guess_clean:
            return {'status': 'partial'}

        # Check for similar artist names
        similarity = SequenceMatcher(None, guess_clean, target_clean).ratio()
        if similarity >= 0.8:
            return {'status': 'partial'}

        return {'status': 'incorrect'}

    @staticmethod
    def compare_years(guess_year, target_year):
        """Compare years with closeness indication"""
        try:
            guess_year = int(str(guess_year)[:4]) if guess_year else 0
            target_year = int(str(target_year)[:4]) if target_year else 0

            if guess_year == target_year:
                return {'status': 'correct'}

            year_diff = abs(guess_year - target_year)

            if year_diff <= 5:
                direction = 'higher' if target_year > guess_year else 'lower'
                return {'status': 'close', 'direction': direction}

            return {'status': 'incorrect'}
        except:
            return {'status': 'incorrect'}

    @staticmethod
    def compare_decades(guess_year, target_year):
        """Compare decades"""
        try:
            guess_decade = (int(str(guess_year)[:4]) // 10) * 10 if guess_year else 0
            target_decade = (int(str(target_year)[:4]) // 10) * 10 if target_year else 0

            if guess_decade == target_decade:
                return {'status': 'correct'}

            return {'status': 'incorrect'}
        except:
            return {'status': 'incorrect'}

    def compare_genres(self, guess_genres, target_genres):
        """Compare genres with partial matching"""
        if not guess_genres or not target_genres:
            return {'status': 'incorrect'}

        # Normalize genres
        guess_genres = [self.normalize_string(g) for g in guess_genres if g]
        target_genres = [self.normalize_string(g) for g in target_genres if g]

        # Check for exact matches
        for guess_genre in guess_genres:
            for target_genre in target_genres:
                # Check if genres are in the same category
                for category, keywords in self.genre_keywords.items():
                    if (any(keyword in guess_genre for keyword in keywords) and
                            any(keyword in target_genre for keyword in keywords)):
                        return {'status': 'partial'}

        return {'status': 'incorrect'}

    @staticmethod
    def compare_tracks(guess_tracks, target_tracks):
        """Compare track counts with closeness indication"""
        try:
            guess_tracks = int(guess_tracks) if guess_tracks else 0
            target_tracks = int(target_tracks) if target_tracks else 0

            if guess_tracks == target_tracks:
                return {'status': 'correct'}

            track_diff = abs(guess_tracks - target_tracks)

            if track_diff <= 3:
                direction = 'higher' if target_tracks > guess_tracks else 'lower'
                return {'status': 'close', 'direction': direction}

            return {'status': 'incorrect'}
        except:
            return {'status': 'incorrect'}

    def is_album_match(self, guess, album_name):
        """Check if the guess matches the album name with fuzzy matching"""
        guess_clean = self.normalize_string(guess)
        album_clean = self.normalize_string(album_name)

        if guess_clean == album_clean:
            return True

        similarity = SequenceMatcher(None, guess_clean, album_clean).ratio()
        return similarity >= 0.9

    @staticmethod
    def normalize_string(text):
        """Normalize string for comparison"""
        if not text:
            return ""
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
