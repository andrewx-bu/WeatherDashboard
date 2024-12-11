import sqlite3
from utils.logger import setup_logger

logger = setup_logger()

def get_db_connection():
    """
    Establish connection to SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object.

    Raises:
        sqlite3.Error: If there is an issue with the database connection.
    """
    try:
        conn = sqlite3.connect('db/weather.db')
        conn.execute('PRAGMA foreign_keys = ON;')
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise