import sqlite3
from utils.logger import setup_logger

def setup_database():
    # Set up the SQLite database with the necessary tables and foreign key constraints.
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()

        # Enable foreign key support
        cursor.execute('PRAGMA foreign_keys = ON;')

        # Create the users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        # Create the favorites table with a foreign key referencing users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        logger.info("Database setup complete")
        print("Database setup complete!")

    except sqlite3.Error as e:
        logger.error(f"An error occurred while setting up the database: {e}")
        print(f"An error occurred while setting up the database: {e}")
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()

if __name__ == "__main__":
    logger = setup_logger()
    setup_database()