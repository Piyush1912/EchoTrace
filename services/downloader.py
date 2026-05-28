import concurrent.futures
import logging
import os
import subprocess
import time
from pathlib import Path

from database.client import new_db_client
from core.fingerprint import fingerprint_audio
from web.utils.utils import generate_song_key

from services.music_metadata import (
    Track,
    get_track_info,
    get_playlist_tracks,
    get_album_tracks,
)
from services.youtube import download_ytaudio, get_youtube_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DELETE_SONG_FILE = False


# Track is imported from services.music_metadata — no duplicate needed


def dl_single_track(url_or_query, save_path):
    """Download a single track. Accepts a Deezer URL or a 'Title - Artist' text search."""
    logger.info(f"Getting track info for: {url_or_query}")
    track_in = get_track_info(url_or_query)
    if not track_in:
        raise ValueError(f"Could not find track metadata for: {url_or_query}")
    return dl_tracks([track_in], save_path)


def dl_playlist(url, save_path):
    """Download all tracks from a Deezer playlist URL."""
    logger.info(f"Getting playlist info for: {url}")
    tracks = get_playlist_tracks(url)
    logger.info(f"Found {len(tracks)} tracks in playlist")
    return dl_tracks(tracks, save_path)


def dl_album(url, save_path):
    """Download all tracks from a Deezer album URL."""
    logger.info(f"Getting album info for: {url}")
    tracks = get_album_tracks(url)
    logger.info(f"Found {len(tracks)} tracks in album")
    return dl_tracks(tracks, save_path)


def dl_tracks(tracks, path):
    total_downloaded = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_track, t, path) for t in tracks]
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                total_downloaded += 1
    logger.info(f"Total tracks downloaded: {total_downloaded}")
    return total_downloaded


def process_track(track, path):
    try:
        # check if song exists
        key_exists = song_key_exists(generate_song_key(track.title, track.artist))
        if key_exists:
            logger.info(f"'{track.title}' by '{track.artist}' already exists.")
            return False

        yt_id = get_youtube_id(track.title, track.artist, track.duration)
        if not yt_id:
            logger.error(f"'{track.title}' by '{track.artist}' could not be downloaded")
            return False

        file_name = f"{track.title} - {track.artist}"
        file_path = Path(path) / file_name

        file_path = download_ytaudio(yt_id, str(file_path))
        if not file_path:
            logger.error(f"'{track.title}' by '{track.artist}' could not be downloaded")
            return False

        if not process_and_save_song(file_path, track.title, track.artist, yt_id):
            return False

        wav_file_path = str(file_path) + ".wav"
        if not add_tags(wav_file_path, track):
            return False

        if DELETE_SONG_FILE:
            delete_file(wav_file_path)

        logger.info(f"'{track.title}' by '{track.artist}' was downloaded")
        return True
    except Exception as e:
        logger.error(f"Error processing track ")
        return False


def add_tags(file, track):
    temp_file = file.replace(".wav", "2.wav")
    cmd = [
        "ffmpeg",
        "-i",
        file,
        "-c",
        "copy",
        "-metadata",
        f"album_artist={track.artist}",
        "-metadata",
        f"title={track.title}",
        "-metadata",
        f"artist={track.artist}",
        "-metadata",
        f"album={track.album or ''}",
        temp_file,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            logger.error(f"Failed to add tags: {out.stderr}")
            return False
        os.replace(temp_file, file)
        return True
    except Exception as e:
        logger.error(f"Failed to add tags: {e}")
        return False


def process_and_save_song(song_file_path, song_title, song_artist, yt_id):
    try:
        dbclient = new_db_client()
        song_id = dbclient.register_song(song_title, song_artist, yt_id)
        fingerprint = fingerprint_audio(song_file_path, song_id)
        dbclient.store_fingerprints(fingerprint)
        logger.info(
            f"Fingerprint for {song_title} by {song_artist} saved in DB successfully"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to process song {song_title}: {e}")
        return False
    finally:
        dbclient.close()
