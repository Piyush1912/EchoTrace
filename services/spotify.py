import json
import math
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()

load_dotenv(dotenv_path=dotenv_path)
# Constants
TOKEN_URL = "https://accounts.spotify.com/api/token"
CACHED_TOKEN_PATH = "token.json"


@dataclass
class Track:
    title: str
    artist: str
    album: str
    artists: List[str]
    duration: int  # seconds


@dataclass
class ResourceEndpoint:
    limit: int = 400
    offset: int = 0
    total_count: int = 0
    requests: int = 0

    def pagination(self):
        self.offset += self.limit


# -------------------------------
# Authentication and Token Handling
# -------------------------------


def load_credentials():
    client_id = os.getenv("CLIENT_ID", "")
    client_secret = os.getenv("CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise RuntimeError("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set")
    return client_id, client_secret


def save_token(token: str, expires_in: int):
    ct = {"token": token, "expires_at": (time.time() + expires_in)}
    with open(CACHED_TOKEN_PATH, "w") as f:
        json.dump(ct, f, indent=2)


def load_cached_token() -> Optional[str]:
    try:
        with open(CACHED_TOKEN_PATH, "r") as f:
            ct = json.load(f)
        if time.time() > ct["expires_at"]:
            return None
        return ct["token"]
    except Exception:
        return None


def access_token() -> str:
    token = load_cached_token()
    if token:
        return token

    client_id, client_secret = load_credentials()
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise RuntimeError(f"Token request failed: {resp.text}")
    tr = resp.json()
    save_token(tr["access_token"], tr["expires_in"])
    return tr["access_token"]


# -------------------------------
# Request Helper
# -------------------------------


def request(endpoint: str):
    bearer = access_token()
    headers = {"Authorization": f"Bearer {bearer}"}
    resp = requests.get(endpoint, headers=headers)
    return resp.status_code, resp.text


def get_id(url: str) -> str:
    parts = url.split("/")
    return parts[4].split("?")[0]


def is_valid_pattern(url: str, pattern: str) -> bool:
    return re.match(pattern, url) is not None


# -------------------------------
# Track Info
# -------------------------------


def track_info(url: str) -> Track:
    re_track = re.compile(
        r"open\.spotify\.com\/(?:intl-.+\/)?track\/([a-zA-Z0-9]{22})(\?si=[a-zA-Z0-9]{16})?"
    )
    matches = re_track.findall(url)
    if not matches:
        raise ValueError("Invalid track URL")
    id_ = matches[0][0]

    endpoint = f"https://api.spotify.com/v1/tracks/{id_}"
    status, json_response = request(endpoint)
    if status != 200:
        raise RuntimeError(f"Non-200 status code: {status}")

    result = json.loads(json_response)
    all_artists = [a["name"] for a in result["artists"]]

    return Track(
        title=result["name"],
        artist=all_artists[0],
        artists=all_artists,
        album=result["album"]["name"],
        duration=result["duration_ms"] // 1000,
    )


# -------------------------------
# Playlist Info
# -------------------------------


def playlist_info(url: str) -> List[Track]:
    re_playlist = re.compile(r"open\.spotify\.com\/playlist\/([a-zA-Z0-9]{22})")
    matches = re_playlist.findall(url)
    if not matches:
        raise ValueError("Invalid playlist URL")
    id_ = matches[0]

    all_tracks = []
    offset = 0
    limit = 100

    while True:
        endpoint = f"https://api.spotify.com/v1/playlists/{id_}/tracks?offset={offset}&limit={limit}"
        status, json_response = request(endpoint)
        if status != 200:
            raise RuntimeError(f"Non-200 status: {status}")

        result = json.loads(json_response)
        for item in result["items"]:
            track = item["track"]
            artists = [a["name"] for a in track["artists"]]
            all_tracks.append(
                Track(
                    title=track["name"],
                    artist=artists[0],
                    artists=artists,
                    duration=track["duration_ms"] // 1000,
                    album=track["album"]["name"],
                )
            )

        offset += limit
        if offset >= result["total"]:
            break

    return all_tracks


# -------------------------------
# Album Info
# -------------------------------


def album_info(url: str) -> List[Track]:
    re_album = re.compile(r"open\.spotify\.com\/album\/([a-zA-Z0-9]{22})")
    matches = re_album.findall(url)
    if not matches:
        raise ValueError("Invalid album URL")
    id_ = matches[0]

    endpoint = f"https://api.spotify.com/v1/albums/{id_}/tracks?limit=50"
    status, json_response = request(endpoint)
    if status != 200:
        raise RuntimeError(f"Non-200 status: {status}")

    result = json.loads(json_response)
    tracks = []
    for item in result["items"]:
        artists = [a["name"] for a in item["artists"]]
        tracks.append(
            Track(
                title=item["name"],
                artist=artists[0],
                artists=artists,
                duration=item["duration_ms"] // 1000,
                album="",  # could fetch full album info if needed
            )
        )
    return tracks
