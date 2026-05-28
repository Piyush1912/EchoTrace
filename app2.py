import os

from flask import Flask, jsonify, render_template, request

from storeNmatch import match_audio

app2 = Flask(__name__)


@app2.route("/")
def index():
    return render_template("index2.html")


@app2.route("/process_audio", methods=["POST"])
def process_audio():
    file = request.files["file"]
    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)
    print(filepath)
    # Call your function
    result, elapsed_t = match_audio(filepath)

    return jsonify({"result": result.song_title})


if __name__ == "__main__":
    app2.run(debug=True)
