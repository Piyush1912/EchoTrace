import subprocess
from dotenv import load_dotenv

# 1. LOAD THIS FIRST!
load_dotenv()
from flask import Flask, render_template, request

from services.fromLinkDownload import downloadViaLink

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    video_url = request.form["video_url"]
    try:
        downloadViaLink(video_url)
        return "Download Started"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
