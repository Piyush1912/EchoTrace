from services.api_call.info import get_token, get_track_id, get_track_info
from services.youtube import (
    convert_duration_to_seconds,
    download_ytaudio,
    get_youtube_id,
)
from core.storeNmatch import match_audio, process_song


def downloadViaLink(url: str):
    token = get_token()
    track_id = get_track_id(spotify_url=url)
    track_info = get_track_info(token=token, track_id=track_id)
    track_name = track_info["name"]
    artists = [artist["name"] for artist in track_info["artists"]]
    duration_ms = track_info["duration_ms"]
    duration = duration_ms / 1000
    print(track_name)
    print(artists)
    print(duration)

    yt_id = get_youtube_id(title=track_name, artist=artists, duration_seconds=duration)
    yt_url = f"https://youtu.be/{yt_id}"
    outfile = "downloaded_songs/%(title)s"
    path = download_ytaudio(video_url=yt_url, output_file_path=outfile, audio_fmt="mp3")
    print("downloaded to:", path)
    process_song(file_path=path, title=track_name, artist=artists, yt_id=yt_id)
