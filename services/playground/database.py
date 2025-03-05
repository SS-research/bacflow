import sqlite3
from datetime import datetime

DB_NAME = "bacflow.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        dob TEXT,
        height REAL,
        weight REAL,
        sex TEXT,
        driver_profile TEXT
    )
    """)
    # Drinks table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS drinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT,
        vol REAL,
        alc_prop REAL,
        time TIMESTAMP,
        sip_interval INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Food table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT,
        time TIMESTAMP,
        category TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

def create_user(username, password, dob, height, weight, sex, driver_profile):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users (username, password, dob, height, weight, sex, driver_profile)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, password, dob, height, weight, sex, driver_profile))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

def get_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_details(user_id, dob, height, weight, sex, driver_profile):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE users SET dob = ?, height = ?, weight = ?, sex = ?, driver_profile = ?
    WHERE id = ?
    """, (dob, height, weight, sex, driver_profile, user_id))
    conn.commit()
    conn.close()

def check_login(username, password):
    user = get_user(username)
    if user and user["password"] == password:
        return user
    return None

def add_drink(user_id, name, vol, alc_prop, time, sip_interval):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO drinks (user_id, name, vol, alc_prop, time, sip_interval)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, vol, alc_prop, time, sip_interval))
    conn.commit()
    drink_id = cur.lastrowid
    conn.close()
    return drink_id

def get_drinks(user_id, from_time, to_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM drinks WHERE user_id = ? AND time BETWEEN ? AND ?
    ORDER BY time ASC
    """, (user_id, from_time, to_time))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_drink(user_id, drink_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM drinks WHERE user_id = ? AND id = ?", (user_id, drink_id))
    conn.commit()
    conn.close()

def update_drink(user_id, drink_id, name, vol, alc_prop, time, sip_interval):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE drinks SET name = ?, vol = ?, alc_prop = ?, time = ?, sip_interval = ?
    WHERE user_id = ? AND id = ?
    """, (name, vol, alc_prop, time, sip_interval, user_id, drink_id))
    conn.commit()
    conn.close()

def add_food(user_id, name, time, category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO food (user_id, name, time, category)
    VALUES (?, ?, ?, ?)
    """, (user_id, name, time, category))
    conn.commit()
    food_id = cur.lastrowid
    conn.close()
    return food_id

def get_food(user_id, from_time, to_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM food WHERE user_id = ? AND time BETWEEN ? AND ?
    ORDER BY time ASC
    """, (user_id, from_time, to_time))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_food(user_id, food_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM food WHERE user_id = ? AND id = ?", (user_id, food_id))
    conn.commit()
    conn.close()

def update_food(user_id, food_id, name, time, category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE food SET name = ?, time = ?, category = ?
    WHERE user_id = ? AND id = ?
    """, (name, time, category, user_id, food_id))
    conn.commit()
    conn.close()
