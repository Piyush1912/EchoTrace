import sqlite3

from database.client import new_db_client
from core.fingerprint import fingerprint_audio
from core.matchSong import find_matches


def process_song(file_path, title, artist, yt_id):
    db = new_db_client()
    try:
        song_id = db.register_song(title, artist, yt_id)
        fingerprints_map = fingerprint_audio(file_path, song_id)
        db.store_fingerprints(fingerprints_map)
        print(f"Stored fingerprints for {title} (ID: {song_id})")
    except Exception as e:
        print("Error during fingerprinting:", e)
        db.delete_song_by_id(song_id)
        print(f"rolled back {song_id} due to error")
    finally:
        db.close()


def match_audio(file_path):
    match, elapsed_t, _ = find_matches(file_path)
    return match, elapsed_t

