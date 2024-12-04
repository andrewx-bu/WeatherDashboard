from dataclasses import dataclass
import logging
import os
import sqlite3
import requests # for API call
from dotenv import load_dotenv # for accessing hidden variables in .env file

from book_collection.utils.logger import configure_logger
from book_collection.utils.random_utils import get_random
from book_collection.utils.sql_utils import get_db_connection


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Book:
    id: int
    author: str
    title: str
    year: int
    genre: str

    def __post_init__(self):
        if self.year <= 1900:
            raise ValueError(f"Year must be greater than 1900, got {self.year}")

def weather() -> None: # just prints current weather description of Boston
    """
    Prints the current weather description of Boston using API Call to OpenWeather Weather API
    
    Args:
        If we need to accept arguments, just take for example city as input

    Returns: 
        None

    Raises:
        If we need to test this we can have us input the city for example
        and then raise an error if it doesn't match "Boston"
    """

    load_dotenv()
    # API key
    API_KEY = os.getenv("OPENWEATHER_API_KEY")

    # URL for current Weather API
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    # Params
    params = {
        "q": "Boston",  # City
        "appid": API_KEY,  # API key
        "units": "imperial"  # 'imperial' for Fahrenheit
    }

    # might change and remove try except...
    try:
        response = requests.get(BASE_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            ### just printing weather description
            # print(f"City: {data['name']}")
            # print(f"Temperature: {data['main']['temp']}°C")
            print(f"Weather: {data['weather'][0]['description']}")
            return None
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None

def create_book(author: str, title: str, year: int, genre: str) -> None:
    """
    Creates a new book in the books table.

    Args:
        author (str): The author's name.
        title (str): The book title.
        year (int): The year the book was released.
        genre (str): The book genre.

    Raises:
        ValueError: If year is invalid.
        sqlite3.IntegrityError: If a book with the same compound key (author, title, year) already exists.
        sqlite3.Error: For any other database errors.
    """
    # Validate the required fields
    if not isinstance(year, int) or year < 1900:
        raise ValueError(f"Invalid year provided: {year} (must be an integer greater than or equal to 1900).")
    
    try:
        # Use the context manager to handle the database connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (author, title, year, genre)
                VALUES (?, ?, ?, ?)
            """, (author, title, year, genre))
            conn.commit()

            logger.info("Book created successfully: %s - %s (%d)", author, title, year)

    except sqlite3.IntegrityError as e:
        logger.error("Book with author '%s', title '%s', and year %d already exists.", author, title, year)
        raise ValueError(f"Book with author '{author}', title '{title}', and year {year} already exists.") from e
    except sqlite3.Error as e:
        logger.error("Database error while creating book: %s", str(e))
        raise sqlite3.Error(f"Database error: {str(e)}")

def clear_catalog() -> None:
    """
    Recreates the books table, effectively deleting all books.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_book_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Catalog cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing catalog: %s", str(e))
        raise e

def delete_book(book_id: int) -> None:
    """
    Soft deletes a book from the catalog by marking it as deleted.

    Args:
        book_id (int): The ID of the book to delete.

    Raises:
        ValueError: If the book with the given ID does not exist or is already marked as deleted.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the book exists and if it's already deleted
            cursor.execute("SELECT deleted FROM books WHERE id = ?", (book_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Book with ID %s has already been deleted", book_id)
                    raise ValueError(f"Book with ID {book_id} has already been deleted")
            except TypeError:
                logger.info("Book with ID %s not found", book_id)
                raise ValueError(f"Book with ID {book_id} not found")

            # Perform the soft delete by setting 'deleted' to TRUE
            cursor.execute("UPDATE books SET deleted = TRUE WHERE id = ?", (book_id,))
            conn.commit()

            logger.info("Book with ID %s marked as deleted.", book_id)

    except sqlite3.Error as e:
        logger.error("Database error while deleting book: %s", str(e))
        raise e

def get_book_by_id(book_id: int) -> Book:
    """
    Retrieves a book from the catalog by its book ID.

    Args:
        book_id (int): The ID of the book to retrieve.

    Returns:
        Book: The Book object corresponding to the book_id.

    Raises:
        ValueError: If the book is not found or is marked as deleted.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to retrieve book with ID %s", book_id)
            cursor.execute("""
                SELECT id, author, title, year, genre, deleted
                FROM books
                WHERE id = ?
            """, (book_id,))
            row = cursor.fetchone()

            if row:
                if row[5]:  # deleted flag
                    logger.info("Book with ID %s has been deleted", book_id)
                    raise ValueError(f"Book with ID {book_id} has been deleted")
                logger.info("Book with ID %s found", book_id)
                return Book(id=row[0], author=row[1], title=row[2], year=row[3], genre=row[4])
            else:
                logger.info("Book with ID %s not found", book_id)
                raise ValueError(f"Book with ID {book_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error while retrieving book by ID %s: %s", book_id, str(e))
        raise e

def get_book_by_compound_key(author: str, title: str, year: int) -> Book:
    """
    Retrieves a book from the catalog by its compound key (author, title, year).

    Args:
        author (str): The author of the book.
        title (str): The title of the book.
        year (int): The year of the book.

    Returns:
        Book: The Book object corresponding to the compound key.

    Raises:
        ValueError: If the book is not found or is marked as deleted.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to retrieve book with author '%s', title '%s', and year %d", author, title, year)
            cursor.execute("""
                SELECT id, author, title, year, genre, deleted
                FROM books
                WHERE author = ? AND title = ? AND year = ?
            """, (author, title, year))
            row = cursor.fetchone()

            if row:
                if row[5]:  # deleted flag
                    logger.info("Book with author '%s', title '%s', and year %d has been deleted", author, title, year)
                    raise ValueError(f"Book with author '{author}', title '{title}', and year {year} has been deleted")
                logger.info("Book with author '%s', title '%s', and year %d found", author, title, year)
                return Book(id=row[0], author=row[1], title=row[2], year=row[3], genre=row[4])
            else:
                logger.info("Book with author '%s', title '%s', and year %d not found", author, title, year)
                raise ValueError(f"Book with author '{author}', title '{title}', and year {year} not found")

    except sqlite3.Error as e:
        logger.error("Database error while retrieving book by compound key (author '%s', title '%s', year %d): %s", author, title, year, str(e))
        raise e

def get_all_books(sort_by_author: bool = False) -> list[dict]:
    """
    Retrieves all books that are not marked as deleted from the catalog.

    Args:
        sort_by_author (bool): If True, sort the books by play count in descending order.

    Returns:
        list[dict]: A list of dictionaries representing all non-deleted books with author.

    Logs:
        Warning: If the catalog is empty.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to retrieve all non-deleted books from the catalog")

            # Determine the sort order based on the 'sort_by_author' flag
            query = """
                SELECT id, author, title, year, genre
                FROM books
                WHERE deleted = FALSE
            """
            if sort_by_author:
                query += " ORDER BY author DESC"

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("The book catalog is empty.")
                return []

            books = [
                {
                    "id": row[0],
                    "author": row[1],
                    "title": row[2],
                    "year": row[3],
                    "genre": row[4],
                }
                for row in rows
            ]
            logger.info("Retrieved %d books from the catalog", len(books))
            return books

    except sqlite3.Error as e:
        logger.error("Database error while retrieving all books: %s", str(e))
        raise e

def get_random_book() -> Book:
    """
    Retrieves a random book from the catalog.

    Returns:
        Book: A randomly selected Book object.

    Raises:
        ValueError: If the catalog is empty.
    """
    try:
        all_books = get_all_books()

        if not all_books:
            logger.info("Cannot retrieve random book because the book catalog is empty.")
            raise ValueError("The book catalog is empty.")

        # Get a random index using the random.org API
        random_index = get_random(len(all_books))
        logger.info("Random index selected: %d (total books: %d)", random_index, len(all_books))

        # Return the book at the random index, adjust for 0-based indexing
        book_data = all_books[random_index - 1]
        return Book(
            id=book_data["id"],
            author=book_data["author"],
            title=book_data["title"],
            year=book_data["year"],
            genre=book_data["genre"]
        )

    except Exception as e:
        logger.error("Error while retrieving random book: %s", str(e))
        raise e
