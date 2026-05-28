"""
fromLinkDownload.py
-------------------
Entry point for downloading a single song via a URL or text search.
Accepts:
  - Deezer track URL  (e.g. https://www.deezer.com/track/123456)
  - Plain text query  (e.g. "Blinding Lights The Weeknd")
"""

from services.music_metadata import get_track_info
from services.youtube import download_ytaudio, get_youtube_id
from core.storeNmatch import process_song


def downloadViaLink(url_or_query: str):
    # 1. Get track metadata (iTunes or Deezer — no API key needed)
    track = get_track_info(url_or_query)
    if not track:
        raise ValueError(f"Could not find track metadata for: {url_or_query}")

    print(f"Title:    {track.title}")
    print(f"Artist:   {track.artist}")
    print(f"Duration: {track.duration_sec}s")

    # 2. Find best YouTube match by duration
    yt_id = get_youtube_id(track.title, track.artist, track.duration_sec)
    if not yt_id:
        raise RuntimeError(f"Could not find a YouTube video for: {track.title} - {track.artist}")

    yt_url = f"https://youtu.be/{yt_id}"
    outfile = "downloaded_songs/%(title)s"

    # 3. Download audio from YouTube
    path = download_ytaudio(video_url=yt_url, output_file_path=outfile, audio_fmt="mp3")
    print("Downloaded to:", path)

    # 4. Fingerprint and store in DB
    process_song(file_path=path, title=track.title, artist=track.artists, yt_id=yt_id)
