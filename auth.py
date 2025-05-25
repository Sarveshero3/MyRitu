import bcrypt
import streamlit as st
import sqlite3
from db import get_db_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def signup_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, hashed_pw, email)
        )
        user_id = cursor.lastrowid
        # Create an empty profile with user_id
        cursor.execute(
            "INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,)
        )
        conn.commit()
        return True, "Signup successful!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password(password, user['password_hash']):
        st.session_state.logged_in = True
        st.session_state.user_id = user['id']
        st.session_state.username = username
        return True, "Login successful!"
    return False, "Invalid username or password."

def logout_user():
    # Clear all relevant session state keys
    keys_to_clear = [
        'logged_in', 'user_id', 'username', 'profile_info', 
        'Ritu_chat_messages', 'show_signup', 'show_profile_modal', 
        'navigate_to_profile', 'initial_profile_setup', 'initial_profile_done',
        'current_tab'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun() # Rerun to go back to login state

def get_user_profile(user_id):
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if profile:
        return dict(profile)
    return {}

def update_user_profile(user_id, profile_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clauses = []
    values = []
    # Ensure all columns from your user_profiles table are potentially updatable here
    valid_profile_columns = [
        'full_name', 'birth_date', 'avg_Ritu_length', 'avg_period_length', 
        'last_period_start', 'medical_conditions', 'medications', 'preferences', 'life_stage'
    ]
    for key, value in profile_data.items():
        if key in valid_profile_columns:
            set_clauses.append(f"{key} = ?")
            values.append(value)
    
    if not set_clauses:
        return False, "No valid fields to update."

    values.append(user_id) # For the WHERE clause
    query = f"UPDATE user_profiles SET {', '.join(set_clauses)} WHERE user_id = ?"
    
    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        # Refresh profile_info in session state after update
        st.session_state.profile_info = get_user_profile(user_id)
        return True, "Profile updated successfully."
    except sqlite3.Error as e:
        print(f"Error in update_user_profile: {e}")
        return False, f"Database error: {e}"
    finally:
        conn.close()