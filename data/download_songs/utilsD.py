from typing import Tuple

from db.client import new_db_client


def song_key_exists(key: str) -> bool:
    db = new_db_client()
    try:
        _, song_exists, _ = db.get_song_by_key(key=key)
        return song_exists
    finally:
        db.close()


import os
import shutil
from pathlib import Path


def delete_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        try:
            if path.is_dir():
                shutil.rmtree(path)  # remove directory and all contents
            else:
                path.unlink()  # remove single file
        except Exception as e:
            raise RuntimeError(f"Failed to delete {file_path}: {e}")
