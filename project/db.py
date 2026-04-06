"""
Database connection helper.
Stored separately from app.py to avoid circular imports.
"""
import sqlite3
from flask import g
from config import Config


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
