import sqlite3
import streamlit as st
from pathlib import Path

_DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


@st.cache_resource
def _get_connection():
    conn = sqlite3.connect(
        _DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                reps INTEGER NOT NULL DEFAULT 0,
                sets INTEGER NOT NULL DEFAULT 0,
                time INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_user(username):
    conn=_get_connection()

    return conn.execute("""
    SELECT * FROM users WHERE username =?
    """,(username)).fetchone()

def create_user(username):
    conn=_get_connection()

    with conn:
        conn.execute("""
        INSERT INTO users (username VALUES (?)
        """,(username))

    return get_user(username)

def get_or_create_user(username):
    user=get_user(username)

    if user is None:
        user=create_user(username)

    return user

def add_exercise(user_id,exercise_name,reps,sets,time):
    conn=_get_connection()

    with conn:
        
