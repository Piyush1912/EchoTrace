import os
import random
import time
import uuid


# from db.client import new_db_client
def generate_unique_id() -> int:
    random.seed(time.time_ns())
    return random.getrandbits(32)


def generate_song_key(song_title: str, song_artist: str) -> str:
    return f"{song_title}---{song_artist}"


def get_env(key: str, fallback: str = "") -> str:
    return os.getenv(key, fallback)


def extend_map(dest: dict, src: dict) -> None:
    dest.update(src)
