DROP TABLE IF EXISTS books;
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    year INTEGER NOT NULL CHECK(year >= 1900),
    genre TEXT NOT NULL,
    --duration INTEGER NOT NULL CHECK(duration > 0),
    --play_count INTEGER DEFAULT 0,
    deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(artist, title, year)
);
