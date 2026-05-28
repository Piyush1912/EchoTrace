import sqlite3
from contextlib import closing

from web.utils import utils


class SQLiteClient:
    def __init__(self, db_path="songs.db"):
        # busy_timeout ~ 5s
        self.conn = sqlite3.connect(db_path, timeout=5.0)
        self.create_tables()

    def create_tables(self):
        with closing(self.conn.cursor()) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    ytID TEXT,
                    key TEXT NOT NULL UNIQUE
                );
            """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fingerprints (
                    address INTEGER NOT NULL,
                    anchorTimeMs INTEGER NOT NULL,
                    songID INTEGER NOT NULL,
                    PRIMARY KEY (address, anchorTimeMs, songID)
                );
            """
            )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def store_fingerprints(self, fingerprints: dict):
        with closing(self.conn.cursor()) as cur:
            for address, couple in fingerprints.items():
                cur.execute(
                    """
                    INSERT OR REPLACE INTO fingerprints (address, anchorTimeMs, songID)
                    VALUES (?, ?, ?)
                """,
                    (address, couple.anchor_time_ms, couple.song_id),
                )
        self.conn.commit()

    def get_couples(self, addresses):
        couples = {}
        with closing(self.conn.cursor()) as cur:
            for address in addresses:
                cur.execute(
                    "SELECT anchorTimeMs, songID FROM fingerprints WHERE address = ?",
                    (address,),
                )
                rows = cur.fetchall()
                couples[address] = [
                    {"anchor_time_ms": r[0], "song_id": r[1]} for r in rows
                ]
        return couples

    def total_songs(self):
        with closing(self.conn.cursor()) as cur:
            cur.execute("SELECT COUNT(*) FROM songs")
            return cur.fetchone()[0]

    def register_song(self, title, artists, ytID):
        artist = ",".join(artists)
        song_key = utils.generate_song_key(title, artist)
        try:
            with closing(self.conn.cursor()) as cur:
                cur.execute(
                    """
                    INSERT INTO songs (title, artist, ytID, key)
                    VALUES (?, ?, ?, ?)
                """,
                    (title, artist, ytID, song_key),
                )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Song with ytID or key already exists")

    def get_song(self, filter_key, value):
        if filter_key not in ("id", "ytID", "key"):
            raise ValueError("Invalid filter key")
        query = f"SELECT title, artist, ytID FROM songs WHERE {filter_key} = ?"
        with closing(self.conn.cursor()) as cur:
            cur.execute(query, (value,))
            row = cur.fetchone()
            if not row:
                return None
            return {"title": row[0], "artist": row[1], "youtube_id": row[2]}

    def get_all_songs(self):
        """Return all songs sorted alphabetically by title."""
        with closing(self.conn.cursor()) as cur:
            cur.execute("SELECT id, title, artist, ytID FROM songs ORDER BY title COLLATE NOCASE ASC")
            rows = cur.fetchall()
            return [
                {"id": r[0], "title": r[1], "artist": r[2], "youtube_id": r[3]}
                for r in rows
            ]

    def get_song_by_id(self, song_id):
        return self.get_song("id", song_id)

    def get_song_by_ytid(self, ytID):
        return self.get_song("ytID", ytID)

    def get_song_by_key(self, key):
        return self.get_song("key", key)

    def delete_song_by_id(self, song_id):
        with closing(self.conn.cursor()) as cur:
            cur.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        self.conn.commit()

    def delete_collection(self, collection_name):
        with closing(self.conn.cursor()) as cur:
            cur.execute(f"DROP TABLE IF EXISTS {collection_name}")
        self.conn.commit()
