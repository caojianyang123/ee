import sqlite3
import bcrypt
import os
import shutil
from src.config import DB_PATH, PROJECTS_ROOT


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            folder_path TEXT NOT NULL,
            github_repo TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()


def register_user(username, password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return dict(user)
    return None


def create_project(user_id, name, description=""):
    folder_path = os.path.join(PROJECTS_ROOT, name)
    os.makedirs(folder_path, exist_ok=True)

    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO projects (user_id, name, description, folder_path) VALUES (?, ?, ?, ?)",
        (user_id, name, description, folder_path)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def get_user_projects(user_id):
    conn = get_conn()
    projects = conn.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(p) for p in projects]


def get_project(project_id):
    conn = get_conn()
    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    conn.close()
    return dict(project) if project else None


def update_project_github(project_id, repo_name):
    conn = get_conn()
    conn.execute(
        "UPDATE projects SET github_repo = ? WHERE id = ?",
        (repo_name, project_id)
    )
    conn.commit()
    conn.close()


def save_chat_message(project_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_history (project_id, role, content) VALUES (?, ?, ?)",
        (project_id, role, content)
    )
    conn.commit()
    conn.close()


def get_chat_history(project_id):
    conn = get_conn()
    messages = conn.execute(
        "SELECT * FROM chat_history WHERE project_id = ? ORDER BY created_at ASC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(m) for m in messages]


def delete_project(project_id):
    project = get_project(project_id)
    if project and os.path.exists(project["folder_path"]):
        shutil.rmtree(project["folder_path"])

    conn = get_conn()
    conn.execute("DELETE FROM chat_history WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()