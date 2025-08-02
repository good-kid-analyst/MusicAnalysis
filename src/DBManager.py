import datetime
from src.MusicWordle import MusicWordleGame

import pymongo


class DBManager:
    def __init__(self, max_guesses=6):
        self.max_guesses = max_guesses
        with pymongo.MongoClient() as c:
            self.db = c.get_database("music-wordle")
            self.games = self.db.get_collection("games")

    def check_active(self, game_id):
        return self.games.find_one({"_id": game_id, "is_completed": False})

    def get_active_games(self) -> list:
        return list(self.games.find({"is_active": True}))

    def get_game_data(self, game_id) -> dict:
        return self.games.find_one({"_id": game_id})

    def new_game(self, game_id, target_album) -> dict:
        obj = {
            "_id": game_id,
            "created_at": datetime.datetime.now(),
            "is_completed": False,
            "is_won": False,
            "n_guesses": 0,
            "max_guesses": self.max_guesses,
            "target_album": target_album,
            "guesses": []
        }
        self.games.insert_one(obj)
        return obj

    def guess(self, music_game: MusicWordleGame, guess):
        music_game.guesses.append(guess)
        music_game.n_guesses += 1
        comparison, is_correct = music_game.compare_albums(guess)
        if is_correct:
            music_game.is_completed = True
            music_game.is_won = True
        elif len(music_game.guesses) >= music_game.max_guesses:
            music_game.is_completed = True
            music_game.is_won = False

        update = {
            "_id": music_game.game_id,
            "created_at": music_game.created_at,
            "is_completed": music_game.is_completed,
            "is_won": music_game.is_won,
            "n_guesses": music_game.n_guesses,
            "max_guesses": music_game.max_guesses,
            "target_album": music_game.target_album,
            "guesses": music_game.guesses
        }

        self.games.update_one({"_id": music_game.game_id}, {"$set": update})
        return is_correct, comparison

    def clean_up(self, cut_off=datetime.datetime.now() - datetime.timedelta(hours=24)):
        update_match = {
            "start_date": {
                "$lte": cut_off,
            },
            "is_completed": False
        }
        self.games.update_many(update_match, {"$set": {"is_completed": True}})
