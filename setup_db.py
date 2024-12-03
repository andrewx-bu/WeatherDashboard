import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

# Create the favorites table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("Database setup complete!")