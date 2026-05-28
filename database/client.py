import os

from database.sqlite import SQLiteClient

# from db.mongo import MongoClient  # Uncomment when you implement mongo.py


def get_env(key: str, default: str = "") -> str:
    """Fetch environment variable with a default fallback."""
    return os.getenv(key, default)


# --- Factory ---
DB_TYPE = get_env("DB_TYPE", "sqlite")  # "sqlite" or "mongo"


def new_db_client():
    """Return a database client depending on DB_TYPE."""
    if DB_TYPE == "mongo":
        db_username = get_env("DB_USER", "")
        db_password = get_env("DB_PASS", "")
        db_name = get_env("DB_NAME", "")
        db_host = get_env("DB_HOST", "localhost")
        db_port = get_env("DB_PORT", "27017")

        if db_username and db_password:
            db_uri = (
                f"mongodb://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
            )
        else:
            db_uri = "mongodb://localhost:27017"

        # return MongoClient(db_uri)   # Placeholder until mongo.py is ready
        raise NotImplementedError("MongoDB client not implemented yet")

    elif DB_TYPE == "sqlite":
        return SQLiteClient("db/db.sqlite3")

    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")
