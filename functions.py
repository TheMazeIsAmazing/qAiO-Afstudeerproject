# Function to establish a connection to the SQLite database
import sqlite3


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries for easier data access
    return conn

# Function to retrieve an account by username (and optionally password)
def get_account(username, password=None):
    conn = get_db_connection()
    if password is None:
        user = conn.execute('SELECT * FROM accounts WHERE username = ?', (username,)).fetchone()
    else:
        user = conn.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (username, password)).fetchone()
    return user  # Return the fetched account information

