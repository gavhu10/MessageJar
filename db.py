import sqlite3
from datetime import datetime

import flask as f


class DBConnection:
    """
    Class-based context manager for a sqlite3.Connection to the database defined
    in the Flask config
    Usage:
        with DBConnection() as db:
            db.execute(...)
    """

    def __init__(self):
        self.conn = None
        self._created_here = False

    def __enter__(self):
        self.conn = sqlite3.connect(
            f.current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        try:
            self.conn.close()
        except Exception:
            pass
        return False


def __close_db(e=None):
    """If this request connected to the database, close the connection."""
    db = f.g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""

    f.current_app.logger.info("Initializing database.")
    with DBConnection() as db:
        with f.current_app.open_resource("schema.sql") as file:
            db.executescript(file.read().decode("utf8"))


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)  # TODO set time zone


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(__close_db)
