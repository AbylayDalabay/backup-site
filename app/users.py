import sqlite3
import random
import string
from config import DATABASES

DATABASE = DATABASES.get('users')

def connect_db():
    return sqlite3.connect(DATABASE)

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def generate_password(length=6):
    return ''.join(random.choices(string.digits, k=length))

def add_user(login, role='viewer'):
    password = generate_password()
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (login, password, role)
        VALUES (?, ?, ?)
        ''', (login, password, role))
        conn.commit()
        print(f"User added: {login}, Password: {password}, Role: {role}")
    except sqlite3.IntegrityError as e:
        print(f"Error adding user: {e}")
    conn.close()

def get_user_by_id(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_login(login):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE login = ?', (login,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'login': user[1],
            'password': user[2],
            'role': user[3]
        }
    else:
        return None

def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def update_user(user_id, login=None, role=None):
    conn = connect_db()
    cursor = conn.cursor()
    if login:
        cursor.execute('UPDATE users SET login = ? WHERE id = ?', (login, user_id))
    if role:
        cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
