from flask import send_from_directory
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
import re
from difflib import SequenceMatcher
import os
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from configparser import ConfigParser

c = ConfigParser()
c.read("config/config.ini")

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a secure secret key
CORS(app, supports_credentials=True)

# Spotify API setup - replace with your credentials
SPOTIFY_CLIENT_ID = c["SPOTIFY"]["CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = c["SPOTIFY"]["CLIENT_SECRET"]

# Initialize Spotify client
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# In-memory storage for games (use database in production)
active_games = {}


class MusicWordleGame:
    def __init__(self, game_id):
        self.game_id = game_id
        self.album_data = None
        self.guesses = []
        self.max_guesses = 6
        self.is_completed = False
        self.is_won = False
        self.created_at = datetime.now()

    def add_guess(self, guess):
        if len(self.guesses) < self.max_guesses and not self.is_completed:
            self.guesses.append(guess)
            return True
        return False

    def check_guess(self, guess):
        if not self.album_data:
            return False

        return self.is_album_match(guess, self.album_data['name'])

    def is_album_match(self, guess, album_name):
        """
        Check if the guess matches the album name with fuzzy matching
        to handle slight variations in spelling or formatting
        """
        # Normalize both strings
        guess_clean = self.normalize_string(guess)
        album_clean = self.normalize_string(album_name)

        # Exact match
        if guess_clean == album_clean:
            return True

        # Fuzzy match with high similarity threshold
        similarity = SequenceMatcher(None, guess_clean, album_clean).ratio()
        return similarity >= 0.9  # 90% similarity threshold

    @staticmethod
    def normalize_string(text):
        """Normalize string for comparison"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def get_random_album():
    """
    Get a random album from Spotify
    You can customize this function based on your existing script
    """
    try:
        # Search for random albums using various genres/decades
        search_queries = [
            'year:1970-1979 genre:rock',
            'year:1980-1989 genre:pop',
            'year:1990-1999 genre:alternative',
            'year:2000-2009 genre:indie',
            'year:2010-2019 genre:electronic',
            'genre:hip-hop',
            'genre:jazz',
            'genre:classical',
            'genre:country',
            'genre:r&b'
        ]

        import random
        query = random.choice(search_queries)

        # Get random offset to get different results
        offset = random.randint(0, 900)  # Spotify limits to 1000

        results = sp.search(
            q=query,
            type='album',
            limit=50,
            offset=offset,
            market='US'
        )

        if results['albums']['items']:
            album = random.choice(results['albums']['items'])

            # Get additional album details
            album_details = sp.album(album['id'])

            # Extract genres (from artists if album doesn't have them)
            genres = album_details.get('genres', [])
            if not genres and album_details['artists']:
                artist_info = sp.artist(album_details['artists'][0]['id'])
                genres = artist_info.get('genres', [])

            return {
                'id': album['id'],
                'name': album['name'],
                'artist': album['artists'][0]['name'] if album['artists'] else 'Unknown',
                'release_date': album.get('release_date', 'Unknown'),
                'year': album.get('release_date', 'Unknown')[:4] if album.get('release_date') else 'Unknown',
                'genres': genres,
                'genre': genres[0] if genres else 'Various',
                'image_url': album['images'][0]['url'] if album['images'] else None,
                'total_tracks': album.get('total_tracks', 0),
                'popularity': album.get('popularity', 0)
            }

    except Exception as e:
        print(f"Error fetching album from Spotify: {e}")
        # Fallback to mock data if Spotify API fails
        return get_mock_album()

    return get_mock_album()


def get_mock_album():
    """Fallback mock data for testing"""
    import random

    mock_albums = [
        {
            'id': 'mock1',
            'name': 'Abbey Road',
            'artist': 'The Beatles',
            'release_date': '1969-09-26',
            'year': '1969',
            'genres': ['rock', 'pop'],
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
            'genres': ['progressive rock', 'psychedelic rock'],
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
        }
    ]

    return random.choice(mock_albums)


@app.route('/api/new-game', methods=['POST'])
def new_game():
    print("/api/new-game")
    """Start a new game with a random album"""
    try:
        # Generate unique game ID
        game_id = str(uuid.uuid4())

        # Get random album
        album_data = get_random_album()

        if not album_data:
            return jsonify({'error': 'Failed to fetch album data'}), 500

        # Create new game
        game = MusicWordleGame(game_id)
        game.album_data = album_data

        # Store game in memory (use database in production)
        active_games[game_id] = game

        # Store game_id in session
        session['game_id'] = game_id

        # Return game info (without album name)
        response_data = {
            'game_id': game_id,
            'artist': album_data['artist'],
            'year': album_data['year'],
            'genre': album_data['genre'],
            'total_tracks': album_data.get('total_tracks'),
            'image_url': album_data.get('image_url'),
            'guesses_remaining': game.max_guesses
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in new_game: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/guess', methods=['POST'])
def check_guess():
    """Check if a guess is correct"""
    try:
        data = request.get_json()

        if not data or 'guess' not in data:
            return jsonify({'error': 'Guess is required'}), 400

        guess = data['guess'].strip()
        if not guess:
            return jsonify({'error': 'Guess cannot be empty'}), 400

        # Get game_id from request or session
        game_id = data.get('game_id') or session.get('game_id')

        if not game_id or game_id not in active_games:
            return jsonify({'error': 'Invalid or expired game'}), 400

        game = active_games[game_id]

        # Check if game is already completed
        if game.is_completed:
            return jsonify({
                'error': 'Game already completed',
                'correct': game.is_won,
                'answer': game.album_data['name'] if game.is_won else None
            }), 400

        # Check if max guesses reached
        if len(game.guesses) >= game.max_guesses:
            return jsonify({'error': 'Maximum guesses reached'}), 400

        # Add guess to game
        if not game.add_guess(guess):
            return jsonify({'error': 'Could not add guess'}), 400

        # Check if guess is correct
        is_correct = game.check_guess(guess)

        # Update game state
        if is_correct:
            game.is_completed = True
            game.is_won = True
        elif len(game.guesses) >= game.max_guesses:
            game.is_completed = True
            game.is_won = False

        response_data = {
            'correct': is_correct,
            'guess_number': len(game.guesses),
            'guesses_remaining': game.max_guesses - len(game.guesses),
            'game_completed': game.is_completed
        }

        # If game is completed, reveal the answer
        if game.is_completed:
            response_data['answer'] = game.album_data['name']
            response_data['album_info'] = {
                'name': game.album_data['name'],
                'artist': game.album_data['artist'],
                'year': game.album_data['year'],
                'genre': game.album_data['genre'],
                'image_url': game.album_data.get('image_url')
            }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in check_guess: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/game-status', methods=['GET'])
def game_status():
    """Get current game status"""
    try:
        game_id = session.get('game_id')

        if not game_id or game_id not in active_games:
            return jsonify({'error': 'No active game'}), 404

        game = active_games[game_id]

        return jsonify({
            'game_id': game_id,
            'guesses': game.guesses,
            'guesses_remaining': game.max_guesses - len(game.guesses),
            'is_completed': game.is_completed,
            'is_won': game.is_won,
            'album_info': {
                'artist': game.album_data['artist'],
                'year': game.album_data['year'],
                'genre': game.album_data['genre']
            }
        })

    except Exception as e:
        print(f"Error in game_status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/hint', methods=['POST'])
def get_hint():
    """Get a hint about the current album"""
    try:
        game_id = session.get('game_id')

        if not game_id or game_id not in active_games:
            return jsonify({'error': 'No active game'}), 404

        game = active_games[game_id]

        if game.is_completed:
            return jsonify({'error': 'Game already completed'}), 400

        # Generate hint based on number of guesses made
        hints = []
        album = game.album_data

        if len(game.guesses) >= 2:
            hints.append(f"This album has {album.get('total_tracks', 'several')} tracks")

        if len(game.guesses) >= 3:
            if album.get('popularity'):
                hints.append(f"Popularity score: {album['popularity']}/100")

        if len(game.guesses) >= 4:
            # Give first letter of album
            hints.append(f"First letter: '{album['name'][0].upper()}'")

        if len(game.guesses) >= 5:
            # Give album length hint
            hints.append(f"Album name has {len(album['name'])} characters")

        return jsonify({
            'hints': hints,
            'available': len(hints) > 0
        })

    except Exception as e:
        print(f"Error in get_hint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# @app.route('/')
# def index():
#     # Read your HTML file and serve it
#     with open('index.html', 'r') as f:
#         html_content = f.read()
#     return html_content

@app.before_request
def cleanup_old_games():
    """Remove games older than 24 hours"""
    try:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)

        games_to_remove = [
            game_id for game_id, game in active_games.items()
            if game.created_at < cutoff_time
        ]

        for game_id in games_to_remove:
            del active_games[game_id]

    except Exception as e:
        print(f"Error cleaning up games: {e}")


if __name__ == '__main__':
    # Make sure to set your Spotify credentials as environment variables:
    # export SPOTIFY_CLIENT_ID="your_client_id"
    # export SPOTIFY_CLIENT_SECRET="your_client_secret"

    print("Starting Music Wordle API...")
    print("Make sure to set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")

    app.run(debug=True, host='0.0.0.0', port=5000)