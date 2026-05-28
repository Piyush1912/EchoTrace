import operator
import time

import web.utils.utils as utils
from database.client import new_db_client
from core.fingerprint import fingerprint_audio


class Match:
    def __init__(self, song_id, title, artist, youtube_id, timestamp, score):
        self.song_id = song_id
        self.song_title = title
        self.song_artist = artist
        self.youtube_id = youtube_id
        self.timestamp = timestamp
        self.score = score

    def __repr__(self):
        return f"<Match {self.song_title} by {self.song_artist} (score={self.score})>"


def find_matches(audio_sample):
    start_time = time.time()
    sample_fingerprint = fingerprint_audio(audio_sample, utils.generate_unique_id())
    sample_fingerprint_map = {
        address: couple.anchor_time_ms for address, couple in sample_fingerprint.items()
    }
    matches, _, _ = find_matches_fgp(sample_fingerprint_map)
    elapsed_time = time.time() - start_time
    return matches[0], elapsed_time, None


def find_matches_fgp(sample_fingerprint):
    start_time = time.time()
    addresses = sample_fingerprint.keys()
    db = new_db_client()
    m = db.get_couples(addresses)
    matches = {}
    timestamp = {}
    target_zones = {}
    for address, couples in m.items():
        for couple in couples:
            song_id = couple["song_id"]
            db_time = couple["anchor_time_ms"]
            sample_time = sample_fingerprint[address]
            matches.setdefault(song_id, []).append((sample_time, db_time))
            if song_id not in timestamp or db_time < timestamp[song_id]:
                timestamp[song_id] = db_time

            target_zones.setdefault(song_id, {})
            target_zones[song_id][db_time] = target_zones[song_id].get(db_time, 0) + 1
    matches_new=filter_matches(5,matches,target_zones)
    scores = analyse_relative_timing(matches_new)
    match_list = []
    for song_id, score in scores.items():
        song = db.get_song_by_id(song_id)
        if song:
            match_list.append(
                Match(
                    song_id,
                    song["title"],
                    song["artist"],
                    song["youtube_id"],
                    timestamp[song_id],
                    score,
                )
            )
   
    match_list.sort(key=operator.attrgetter("score"), reverse=True)
    elapsed = time.time() - start_time
    return match_list, elapsed, None


def filter_matches(threshold, matches, target_zones, target_zone_size=3):
    for song_id, anchor_times in target_zones.items():
        for anchor_time, count in list(anchor_times.items()):
            if count < target_zone_size:
                del target_zones[song_id][anchor_time]

    filtered = {}
    for song_id, zones in target_zones.items():
        if len(zones) >= threshold:
            filtered[song_id] = matches[song_id]
    return filtered


def analyse_relative_timing(matches):
    scores = {}
    for song_id, times in matches.items():
        offset_count = {}
        for sample_time, db_time in times:
            offset = db_time - sample_time
            offset_bucket = offset // 100
            offset_count[offset_bucket] = offset_count.get(offset_bucket, 0) + 1

        scores[song_id] = max(offset_count.values()) if offset_count else 0
    return scores
