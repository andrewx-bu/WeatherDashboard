import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()

# Create the weather_log table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        temperature REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("Database setup complete!")