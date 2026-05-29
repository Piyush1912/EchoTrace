# EchoTrace 🎵

EchoTrace is a self-hosted, lightweight, and modern song recognition web application. It allows you to identify playing music using audio fingerprinting technology (similar to Shazam) and build your own local library of fingerprinted tracks.

The application features a sleek, premium **dark glassmorphism user interface** with live animations, responsive tabs, and micro-interactions.

---

## Features

### 🎤 1. Real-time Song Recognition
* Identify songs playing around you in seconds.
* Record a 10-second audio clip directly from your microphone via the browser using standard Web Audio APIs.
* Matches the recording's acoustic fingerprint against your local SQLite database and returns the song details, matching score, search duration, and a direct YouTube watch link.

### ➕ 2. Search-as-you-type Song Ingestion
* Add new songs to your library by searching for track names.
* Displays live search suggestions as you type (powered by the iTunes Search API, no keys required).
* Shows track title, artist, album, and duration to prevent naming ambiguity.
* **Direct Download**: Download and index a song immediately by clicking the cloud download button on any suggestion.
* **Metadata Preservation**: Populates the search bar when selecting suggestions, ready for fingerprinting.
* **Deezer Link Support**: Paste direct Deezer tracks, playlists, or album URLs to ingest them in bulk.

### 🎶 3. Interactive Song Library
* View a list of all fingerprinted songs currently in your database.
* Instantly search and filter through your library locally.
* Quick-access buttons to play or watch any of your fingerprinted songs on YouTube.
* Live library status showing the total index count.

---

## Technology Stack

* **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Custom Dark Glassmorphic Theme with CSS variables, blur filters, and transitions).
* **Backend**: Flask (Python 3.9+).
* **Database**: SQLite3 (File-based database storing track details and acoustic fingerprints).
* **Metadata Services**: iTunes Search API (Primary) and Deezer API (Fallback) — completely free and keyless.
* **Media Downloader**: `yt-dlp` for locating and downloading high-quality audio files from YouTube.
* **Audio Processing**: `scipy`, `numpy`, and `librosa` for audio parsing, spectrogram generation, and peak-matching.

---

## Installation & Setup

### Prerequisites
Make sure you have **FFmpeg** installed on your system. It is required by `yt-dlp` to extract and convert audio streams to MP3s.

* **macOS** (via Homebrew):
  ```bash
  brew install ffmpeg
  ```
* **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install ffmpeg
  ```
* **Windows**: Download the binaries from [ffmpeg.org](https://ffmpeg.org/download.html) and add them to your System PATH.

---

### Step-by-Step Run Guide

1. **Clone or Navigate to the Directory**:
   ```bash
   cd song_recognition
   ```

2. **Set Up a Python Virtual Environment**:
   ```bash
   # Create environment
   python3 -m venv myenv

   # Activate environment
   source myenv/bin/activate  # On Windows, use: myenv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install yt-dlp
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Access the Web Interface**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

---

## File Structure

```text
├── app.py                      # Flask application and REST routes
├── templates/
│   └── index.html              # Frontend page containing HTML, CSS, and JS
├── services/
│   ├── music_metadata.py       # Keyless iTunes and Deezer metadata fetchers
│   ├── youtube.py              # yt-dlp search wrapper for finding YouTube IDs
│   ├── fromLinkDownload.py     # Pipeline for downloading, converting, and indexing songs
│   └── downloader.py           # Core file downloader utilities
├── core/
│   ├── storeNmatch.py          # Entry point for fingerprint extraction and DB query matches
│   └── fingerprint.py          # Acoustic fingerprinting algorithms (peaks, hashes)
├── database/
│   ├── client.py               # Database client factory
│   └── sqlite.py               # SQLite adapter class
├── data/
│   ├── db.sqlite3              # Active SQLite database file
│   └── uploads/                # Temporary directory for uploading microphone recordings
└── downloaded_songs/           # Directory where downloaded MP3 tracks are stored
```

---

## License

This project is open-source and free to use. Built with ❤️ for music enthusiasts.
