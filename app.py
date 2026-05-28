"""
app.py — Unified Song Recognition App
Combines song recognition (mic) + song ingestion (Deezer/text search)
"""

from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, request, jsonify
from core.storeNmatch import match_audio, process_song
from services.fromLinkDownload import downloadViaLink

app = Flask(__name__)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Recognize: mic audio → match ──────────────────────────────────────────────

@app.route("/recognize", methods=["POST"])
def recognize():
    if "file" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filepath = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)

    try:
        match, elapsed = match_audio(filepath)
        if match is None:
            return jsonify({"error": "No match found"}), 404
        return jsonify({
            "title":      match.song_title,
            "artist":     match.song_artist,
            "youtube_id": match.youtube_id,
            "score":      match.score,
            "elapsed":    round(elapsed, 2),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)


# ── Ingest: Deezer URL or text → download + fingerprint ──────────────────────

@app.route("/add-song", methods=["POST"])
def add_song():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No song query provided"}), 400

    try:
        downloadViaLink(query)
        return jsonify({"status": "Song added and fingerprinted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
