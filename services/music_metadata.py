"""
music_metadata.py
-----------------
Free, no-API-key music metadata fetching.
Primary:  iTunes Search API  (Apple) — 20 req/min, no auth
Fallback: Deezer API          — 50 req/5s, no auth

Replaces the old services/spotify.py and services/api_call/info.py
"""

import re
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Shared data model
# ──────────────────────────────────────────────

@dataclass
class Track:
    title: str
    artist: str
    album: str = ""
    duration_sec: int = 0        # always in whole seconds
    artists: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.artists:
            self.artists = [self.artist]


# ──────────────────────────────────────────────
# iTunes Search API  (primary)
# https://itunes.apple.com/search
# ──────────────────────────────────────────────

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


def _itunes_request(params: dict) -> Optional[dict]:
    try:
        resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"iTunes request failed: {e}")
        return None


def _itunes_result_to_track(r: dict) -> Track:
    duration_ms = r.get("trackTimeMillis", 0) or 0
    artists = [r.get("artistName", "Unknown")]
    return Track(
        title=r.get("trackName", "Unknown"),
        artist=artists[0],
        album=r.get("collectionName", ""),
        duration_sec=duration_ms // 1000,
        artists=artists,
    )


def itunes_search_track(title: str, artist: str = "", limit: int = 10) -> List[Track]:
    """Search iTunes for a track by title (+ optional artist)."""
    term = f"{title} {artist}".strip()
    data = _itunes_request({"term": term, "media": "music", "entity": "song", "limit": limit})
    if not data:
        return []
    return [_itunes_result_to_track(r) for r in data.get("results", [])]


def itunes_track_info(title: str, artist: str = "") -> Optional[Track]:
    """Return the single best-matching track from iTunes."""
    results = itunes_search_track(title, artist, limit=5)
    return results[0] if results else None


# ──────────────────────────────────────────────
# Deezer API  (fallback + playlist/album support)
# https://api.deezer.com
# ──────────────────────────────────────────────

DEEZER_BASE = "https://api.deezer.com"

_DEEZER_TRACK_RE = re.compile(r"deezer\.com(?:/[a-z]{2})?/track/(\d+)")
_DEEZER_PLAYLIST_RE = re.compile(r"deezer\.com(?:/[a-z]{2})?/playlist/(\d+)")
_DEEZER_ALBUM_RE = re.compile(r"deezer\.com(?:/[a-z]{2})?/album/(\d+)")


def _deezer_get(path: str) -> Optional[dict]:
    try:
        resp = requests.get(f"{DEEZER_BASE}{path}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            logger.warning(f"Deezer error: {data['error']}")
            return None
        return data
    except Exception as e:
        logger.warning(f"Deezer request failed: {e}")
        return None


def _deezer_item_to_track(item: dict) -> Track:
    artist_name = item.get("artist", {}).get("name", "Unknown")
    album_title = item.get("album", {}).get("title", "")
    return Track(
        title=item.get("title", "Unknown"),
        artist=artist_name,
        album=album_title,
        duration_sec=int(item.get("duration", 0)),
        artists=[artist_name],
    )


def deezer_track_info(url: str) -> Optional[Track]:
    """Fetch a single track from a Deezer track URL."""
    m = _DEEZER_TRACK_RE.search(url)
    if not m:
        raise ValueError(f"Not a valid Deezer track URL: {url}")
    data = _deezer_get(f"/track/{m.group(1)}")
    return _deezer_item_to_track(data) if data else None


def deezer_playlist_info(url: str) -> List[Track]:
    """Fetch all tracks from a Deezer playlist URL."""
    m = _DEEZER_PLAYLIST_RE.search(url)
    if not m:
        raise ValueError(f"Not a valid Deezer playlist URL: {url}")

    tracks = []
    index = 0
    while True:
        data = _deezer_get(f"/playlist/{m.group(1)}/tracks?index={index}&limit=100")
        if not data:
            break
        items = data.get("data", [])
        tracks.extend(_deezer_item_to_track(i) for i in items)
        if data.get("next"):
            index += 100
            time.sleep(0.1)   # be polite to Deezer
        else:
            break
    return tracks


def deezer_album_info(url: str) -> List[Track]:
    """Fetch all tracks from a Deezer album URL."""
    m = _DEEZER_ALBUM_RE.search(url)
    if not m:
        raise ValueError(f"Not a valid Deezer album URL: {url}")

    data = _deezer_get(f"/album/{m.group(1)}/tracks")
    if not data:
        return []

    # album endpoint doesn't nest artist/album in each track, fetch album info
    album_data = _deezer_get(f"/album/{m.group(1)}")
    album_title = album_data.get("title", "") if album_data else ""
    album_artist = album_data.get("artist", {}).get("name", "Unknown") if album_data else "Unknown"

    tracks = []
    for item in data.get("data", []):
        artist_name = item.get("artist", {}).get("name", album_artist)
        tracks.append(Track(
            title=item.get("title", "Unknown"),
            artist=artist_name,
            album=album_title,
            duration_sec=int(item.get("duration", 0)),
            artists=[artist_name],
        ))
    return tracks


def deezer_search_track(title: str, artist: str = "", limit: int = 10) -> List[Track]:
    """Search Deezer for a track by title + optional artist."""
    query = f'track:"{title}"'
    if artist:
        query += f' artist:"{artist}"'
    data = _deezer_get(f"/search/track?q={requests.utils.quote(query)}&limit={limit}")
    if not data:
        return []
    return [_deezer_item_to_track(i) for i in data.get("data", [])]


# ──────────────────────────────────────────────
# Unified public API
# ──────────────────────────────────────────────

def _is_deezer_url(url: str) -> bool:
    return "deezer.com" in url


def get_track_info(url_or_query: str, artist: str = "") -> Optional[Track]:
    """
    Get a single track's metadata.
    - Accepts a Deezer track URL  →  uses Deezer API
    - Accepts a plain text query  →  tries iTunes, falls back to Deezer
    """
    if _is_deezer_url(url_or_query):
        return deezer_track_info(url_or_query)

    # text search: iTunes first, Deezer fallback
    track = itunes_track_info(url_or_query, artist)
    if track:
        return track
    logger.info("iTunes returned no result, trying Deezer search...")
    results = deezer_search_track(url_or_query, artist, limit=5)
    return results[0] if results else None


def get_playlist_tracks(url: str) -> List[Track]:
    """
    Get all tracks from a playlist URL.
    Currently supports: Deezer playlists.
    """
    if _is_deezer_url(url):
        return deezer_playlist_info(url)
    raise ValueError("Only Deezer playlist URLs are supported (Spotify removed free API access).")


def get_album_tracks(url: str) -> List[Track]:
    """
    Get all tracks from an album URL.
    Currently supports: Deezer albums.
    """
    if _is_deezer_url(url):
        return deezer_album_info(url)
    raise ValueError("Only Deezer album URLs are supported (Spotify removed free API access).")
