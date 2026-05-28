import json
import os

from dotenv import find_dotenv, load_dotenv


print("ENV PATH:", find_dotenv())       # Is it finding the .env?
print("CLIENT_ID:", os.getenv("CLIENT_ID"))  # Is it None?
pa = find_dotenv()
print(pa)
load_dotenv()
import base64

import requests
from requests import post

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


def get_token():
    auth_string = client_id + ":" + client_secret
    auth_encoded = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_encoded), "utf-8")
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    if result.status_code != 200:
        print(f"Error fetching token: {result.text}") # This will show you the HTML/Error!
        return None
    json_result = json.loads(result.content)

    token = json_result["access_token"]
    return token


def get_track_id(spotify_url):
    return spotify_url.split("/")[-1].split("?")[0]


def get_track_info(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": "Bearer " + token}
    result = requests.get(url, headers=headers)
    return result.json()
