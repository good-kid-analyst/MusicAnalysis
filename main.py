from flask import Flask, request, jsonify, session
from flask_cors import CORS
import uuid
from datetime import datetime, timedelta
from configparser import ConfigParser
from src.SpotifyManager import SpotifyManager
from src.MusicWordle import MusicWordleGame
from src.DBManager import DBManager

c = ConfigParser()
c.read("config/config.ini")

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a secure secret key
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie_name'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Helps with CSRF protection

CORS(app, supports_credentials=True,
     # resources={
     # r"/api/*": {
     #     "origins": ["http://localhost:5000"],  # Or whatever your frontend origin is
     #     "methods": ["GET", "POST", "OPTIONS"],
     #     "allow_headers": ["Content-Type"],
     #     "supports_credentials": True
     # }
     # }
     )

s = SpotifyManager()
db = DBManager()


@app.route('/api/new-game', methods=['POST'])
def new_game():
    """Start a new game with a random album"""
    try:
        game_id = str(uuid.uuid4())
        target_album = s.get_random_album()
        if not target_album:
            return jsonify({'error': 'Failed to fetch album data'}), 500

        current_game = db.new_game(game_id, target_album)

        # Don't reveal the album name in response
        response_data = {
            'game_id': game_id,
            'message': 'New game started! Start guessing!',
            'max_guesses': current_game["max_guesses"]
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in new_game: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/search-albums', methods=['POST'])
def search_albums_endpoint():
    """Search for albums"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query = data['query'].strip()
        if len(query) < 2:
            return jsonify({'albums': []}), 200

        albums = s.search_albums(query, limit=10)
        return jsonify({'albums': albums})

    except Exception as e:
        print(f"Error in search_albums: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/guess', methods=['POST'])
def check_guess():
    """Check a guess and return detailed comparison"""
    data = request.get_json()
    if not data or 'album_id' not in data:
        return jsonify({'error': 'Album ID is required'}), 400
    game_id = data['game_id']

    if not game_id or not db.check_active(game_id):
        return jsonify({'error': 'Invalid or expired game'}), 400

    game = db.get_game_data(game_id)
    music_game = MusicWordleGame(**game)

    if music_game.is_completed:
        return jsonify({'error': 'Game already completed'}), 400

    if len(game["guesses"]) >= game["max_guesses"]:
        return jsonify({'error': 'Maximum guesses reached'}), 400

    # Get album details for the guess
    guessed_album_id = data['album_id']
    guessed_album = None

    # Try to get album details from Spotify
    if s.sp:
        try:
            album_details = s.sp.album(guessed_album_id)
            # Get genres from artist
            genres = album_details.get('genres', [])
            if not genres and album_details['artists']:
                artist_info = s.sp.artist(album_details['artists'][0]['id'])
                genres = artist_info.get('genres', [])

            guessed_album = {
                'id': album_details['id'],
                'name': album_details['name'],
                'artist': album_details['artists'][0]['name'] if album_details['artists'] else 'Unknown',
                'year': album_details.get('release_date', '')[:4] if album_details.get('release_date') else '',
                'genres': genres[:3],
                'genre': genres[0] if genres else 'Various',
                'total_tracks': album_details.get('total_tracks', 0)
            }
        except Exception as e:
            print(f"Error fetching album details: {e}")

    # Fallback to mock data or search results
    if not guessed_album:
        # Try to find in mock data
        mock_albums = [
            {'id': 'mock1', 'name': 'Abbey Road', 'artist': 'The Beatles', 'year': '1969', 'genres': ['rock'],
             'genre': 'Rock', 'total_tracks': 17},
            {'id': 'mock2', 'name': 'Dark Side of the Moon', 'artist': 'Pink Floyd', 'year': '1973',
             'genres': ['progressive rock'], 'genre': 'Progressive Rock', 'total_tracks': 10},
            {'id': 'mock3', 'name': 'Thriller', 'artist': 'Michael Jackson', 'year': '1982', 'genres': ['pop'],
             'genre': 'Pop', 'total_tracks': 9},
            {'id': 'mock4', 'name': 'Nevermind', 'artist': 'Nirvana', 'year': '1991', 'genres': ['grunge'],
             'genre': 'Grunge', 'total_tracks': 12}
        ]

        guessed_album = next((album for album in mock_albums if album['id'] == guessed_album_id), None)

    if not guessed_album:
        return jsonify({'error': 'Album not found'}), 400

    # Add guess to game
    is_correct, comparison = db.guess(music_game, guessed_album)

    # Compare albums
    response_data = {
        'correct': is_correct,
        'comparison': comparison,
        'guess_number': len(game["guesses"]),
        'guesses_remaining': game["max_guesses"] - len(game["guesses"]),
        'game_completed': game["is_completed"]
    }

    # If game is completed, reveal the answer
    if game["is_completed"]:
        response_data['target_album'] = game["target_album"]

    return jsonify(response_data)


@app.route('/api/game-status', methods=['GET'])
def game_status():
    """Get current game status"""
    try:
        game_id = session.get('game_id')

        if not game_id or not db.check_active(game_id):
            return jsonify({'error': 'No active game'}), 404

        game = db.get_game_data(game_id)

        return jsonify({
            'game_id': game_id,
            'guess_count': len(game["guesses"]),
            'guesses_remaining': game["max_guesses"] - len(game["guesses"]),
            'is_completed': game["is_completed"],
            'is_won': game["is_won"],
            'max_guesses': game["max_guesses"]
        })

    except Exception as e:
        print(f"Error in game_status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


# Cleanup old games periodically
@app.before_request
def cleanup_old_games():
    """Remove games older than 24 hours"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        db.clean_up(cutoff_time)
    except Exception as e:
        print(f"Error cleaning up games: {e}")


if __name__ == '__main__':
    print("Starting Music Wordle API...")
    print("Available endpoints:")
    print("  POST /api/new-game - Start new game")
    print("  POST /api/search-albums - Search for albums")
    print("  POST /api/guess - Submit a guess")
    print("  GET /api/game-status - Get game status")

    app.run(debug=True, host='0.0.0.0', port=5000)
