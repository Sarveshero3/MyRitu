import sqlite3
import datetime
import json

DATABASE_NAME = 'MyRitu.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table (no changes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # User profiles table (no changes from previous version with life_stage)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            birth_date TEXT,
            avg_Ritu_length INTEGER DEFAULT 28,
            avg_period_length INTEGER DEFAULT 5,
            last_period_start TEXT,
            medical_conditions TEXT,
            medications TEXT,
            preferences TEXT,
            life_stage TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN life_stage TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column likely already exists

    # Ritu data table (no changes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ritu_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            period_start_date TEXT NOT NULL,
            period_end_date TEXT,
            symptoms TEXT,
            notes TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # --- New Chat Logs Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sender TEXT NOT NULL, -- "user" or "bot"
            message TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Functions for Chat Logs ---
def log_chat_message(user_id, sender, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_logs (user_id, sender, message) VALUES (?, ?, ?)",
            (user_id, sender, message)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error logging chat message: {e}")
        return False
    finally:
        conn.close()

def get_chat_history_from_db(user_id, limit=50): # Get recent messages for display
    conn = get_db_connection()
    messages = conn.execute(
        "SELECT sender, message FROM chat_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    # Return in chronological order for display
    return [{"sender": msg["sender"], "message": msg["message"]} for msg in reversed(messages)]


# --- Function to Delete User Data (Factory Reset) ---
def delete_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Order of deletion matters due to foreign key constraints if ON DELETE CASCADE is not set
        # For simplicity, we assume ON DELETE CASCADE is not strictly enforced by default in SQLite python lib
        # or that we delete in an order that respects dependencies.
        cursor.execute("DELETE FROM chat_logs WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM Ritu_data WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "All your data has been successfully deleted."
    except sqlite3.Error as e:
        print(f"Error deleting user data: {e}")
        return False, f"An error occurred while deleting your data: {e}"
    finally:
        conn.close()

# Existing functions (log_period_data, get_Ritu_history) remain the same
def log_period_data(user_id, period_start_date, period_end_date=None, symptoms=None, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        symptoms_json = json.dumps(symptoms) if symptoms else None
        cursor.execute(
            """INSERT INTO Ritu_data 
               (user_id, period_start_date, period_end_date, symptoms, notes) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, period_start_date, period_end_date, symptoms_json, notes)
        )
        conn.commit()
        return True, "Period data logged successfully."
    except sqlite3.Error as e:
        print(f"Error in log_period_data: {e}")
        return False, f"Database error: {e}"
    finally:
        conn.close()

def get_Ritu_history(user_id):
    conn = get_db_connection()
    history_cursor = conn.execute(
        "SELECT * FROM Ritu_data WHERE user_id = ? ORDER BY period_start_date DESC",
        (user_id,)
    )
    history_rows = history_cursor.fetchall()
    conn.close()
    processed_history = []
    for row in history_rows:
        item = dict(row)
        if item.get('symptoms'):
            try: item['symptoms'] = json.loads(item['symptoms'])
            except json.JSONDecodeError: item['symptoms'] = {} 
        processed_history.append(item)
    return processed_history

if __name__ == '__main__':
    print("Database initialized/checked (db.py executed).")