import sqlite3
import os
import hashlib
import uuid
from datetime import datetime

DB_FILE = "shots_app.db"

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables if they don't exist"""
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create projects table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create shots table to save generated shots
    conn.execute('''
    CREATE TABLE IF NOT EXISTS shots (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        scene_description TEXT NOT NULL,
        genre TEXT NOT NULL,
        mood TEXT NOT NULL,
        model_name TEXT NOT NULL,
        shot_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# User management functions
def create_user(username, email, password):
    """Create a new user account"""
    conn = get_db_connection()
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, username, email, password_hash)
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate a user by username and password"""
    conn = get_db_connection()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    ).fetchone()
    
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

# Project management functions
def create_project(user_id, name, description=""):
    """Create a new project"""
    conn = get_db_connection()
    project_id = str(uuid.uuid4())
    
    conn.execute(
        "INSERT INTO projects (id, user_id, name, description) VALUES (?, ?, ?, ?)",
        (project_id, user_id, name, description)
    )
    conn.commit()
    conn.close()
    return project_id

def get_user_projects(user_id):
    """Get all projects for a user"""
    conn = get_db_connection()
    projects = conn.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(project) for project in projects]

def get_project(project_id):
    """Get project by ID"""
    conn = get_db_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(project) if project else None

def delete_project(project_id):
    """Delete a project and its shots"""
    conn = get_db_connection()
    # First delete related shots
    conn.execute("DELETE FROM shots WHERE project_id = ?", (project_id,))
    # Then delete the project
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# Shot management functions
def save_shot_results(project_id, scene_description, genre, mood, model_name, shot_data):
    """Save generated shot results"""
    conn = get_db_connection()
    shot_id = str(uuid.uuid4())
    
    conn.execute(
        """INSERT INTO shots 
           (id, project_id, scene_description, genre, mood, model_name, shot_data) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (shot_id, project_id, scene_description, genre, mood, model_name, shot_data)
    )
    conn.commit()
    conn.close()
    return shot_id

def get_project_shots(project_id):
    """Get all shots for a project"""
    conn = get_db_connection()
    shots = conn.execute(
        "SELECT * FROM shots WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(shot) for shot in shots]

def get_shot(shot_id):
    """Get shot by ID"""
    conn = get_db_connection()
    shot = conn.execute("SELECT * FROM shots WHERE id = ?", (shot_id,)).fetchone()
    conn.close()
    return dict(shot) if shot else None

# Initialize the database on import
init_db()