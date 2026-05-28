import concurrent.futures
import logging
import os
import subprocess
import time
from pathlib import Path

from database.client import new_db_client
from data.download_songs.utilsD import delete_file, song_key_exists
from core.fingerprint import fingerprint_audio
from web.utils.utils import generate_song_key

from services.spotify import album_info, playlist_info, track_info
from services.youtube import download_ytaudio, get_youtube_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify")

DELETE_SONG_FILE = False


class Track:
    def __init__(self, title, artist, album=None, duration=None, artists=None):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.artists = artists or []


def dl_single_track(url, save_path):
    logger.info("Getting track info", extra={"url": url})
    track_in = track_info(url)
    tracks = [track_in]
    logger.info("Now downloading track")
    return dl_tracks(tracks, save_path)


def dl_playlist(url, save_path):
    logger.info("Getting playlist info", extra={"url": url})
    tracks = playlist_info(url)  # placeholder
    time.sleep(1)
    logger.info("Now downloading playlist")
    return dl_tracks(tracks, save_path)


def dl_album(url, save_path):
    logger.info("Getting album info", extra={"url": url})
    tracks = album_info(url)  # placeholder
    time.sleep(1)
    logger.info("Now downloading album")
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

        yt_id = get_youtube_id(track)
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
