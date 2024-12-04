from contextlib import contextmanager
import re
import sqlite3

import pytest

from book_collection.models.book_model import (
    Book,
    create_book,
    clear_catalog,
    delete_book,
    get_book_by_id,
    get_book_by_compound_key,
    get_all_books,
    get_random_book
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("book_collection.models.book_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_book(mock_cursor):
    """Test creating a new book in the catalog."""

    # Call the function to create a new book
    create_book(author="Author Name", title="Book Title", year=2022, genre="Fiction")

    expected_query = normalize_whitespace("""
        INSERT INTO books (author, title, year, genre)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Author Name", "Book Title", 2022, "Fiction")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_book_duplicate(mock_cursor):
    """Test creating a book with a duplicate author, title, and year (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: books.author, books.title, books.year")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Book with author 'Author Name', title 'Book Title', and year 2022 already exists."):
        create_book(author="Author Name", title="Book Title", year=2022, genre="Fiction")

def test_create_book_invalid_year():
    """Test error when trying to create a book with an invalid year (e.g., less than 1900 or non-integer)."""

    # Attempt to create a book with a year less than 1900
    with pytest.raises(ValueError, match="Invalid year provided: 1899 \(must be an integer greater than or equal to 1900\)."):
        create_book(author="Author Name", title="Book Title", year=1899, genre="Drama")

    # Attempt to create a book with a non-integer year
    with pytest.raises(ValueError, match="Invalid year provided: invalid \(must be an integer greater than or equal to 1900\)."):
        create_book(author="Author Name", title="Book Title", year="invalid", genre="Drama")

def test_delete_book(mock_cursor):
    """Test soft deleting a book from the catalog by book ID."""

    # Simulate that the book exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_book function
    delete_book(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM books WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE books SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_book_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent book."""

    # Simulate that no book exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent book
    with pytest.raises(ValueError, match="Book with ID 999 not found"):
        delete_book(999)

def test_delete_book_already_deleted(mock_cursor):
    """Test error when trying to delete a book that's already marked as deleted."""

    # Simulate that the book exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a book that's already been deleted
    with pytest.raises(ValueError, match="Book with ID 999 has already been deleted"):
        delete_book(999)

def test_clear_catalog(mock_cursor, mocker):
    """Test clearing the entire book catalog (removes all books)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_book_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_catalog()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_book_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get Book
#
######################################################

def test_get_book_by_id(mock_cursor):
    # Simulate that the book exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Author Name", "Book Title", 2022, "Fiction", False)

    # Call the function and check the result
    result = get_book_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Book(1, "Author Name", "Book Title", 2022, "Fiction")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, author, title, year, genre, deleted FROM books WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_book_by_id_bad_id(mock_cursor):
    # Simulate that no book exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the book is not found
    with pytest.raises(ValueError, match="Book with ID 999 not found"):
        get_book_by_id(999)

def test_get_book_by_compound_key(mock_cursor):
    # Simulate that the book exists (author = "Author Name", title = "Book Title", year = 2022)
    mock_cursor.fetchone.return_value = (1, "Author Name", "Book Title", 2022, "Fiction", False)

    # Call the function and check the result
    result = get_book_by_compound_key("Author Name", "Book Title", 2022)

    # Expected result based on the simulated fetchone return value
    expected_result = Book(1, "Author Name", "Book Title", 2022, "Fiction")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, author, title, year, genre, deleted FROM books WHERE author = ? AND title = ? AND year = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Author Name", "Book Title", 2022)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_all_books(mock_cursor):
    """Test retrieving all books that are not marked as deleted."""

    # Simulate that there are multiple books in the database
    mock_cursor.fetchall.return_value = [
        (1, "Harper Lee", "To Kill a Mockingbird", 1960, "Novel", False),
        (2, "George Orwell", "1984", 1949, "Science Fiction", False),
        (3, "J.D. Salinger", "The Catcher in the Rye", 1951, "Novel", False)
    ]

    # Call the get_all_books function
    books = get_all_books()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "author": "Harper Lee", "title": "To Kill a Mockingbird", "year": 1960, "genre": "Novel"},
        {"id": 2, "author": "George Orwell", "title": "1984", "year": 1949, "genre": "Science Fiction"},
        {"id": 3, "author": "J.D. Salinger", "title": "The Catcher in the Rye", "year": 1951, "genre": "Novel"}
    ]

    assert books == expected_result, f"Expected {expected_result}, but got {books}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, author, title, year, genre
        FROM books
        WHERE deleted = FALSE
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_all_books_empty_catalog(mock_cursor, caplog):
    """Test that retrieving all books returns an empty list when the catalog is empty and logs a warning."""

    # Simulate that the catalog is empty (no books)
    mock_cursor.fetchall.return_value = []

    # Call the get_all_books function
    result = get_all_books()

    # Ensure the result is an empty list
    assert result == [], f"Expected empty list, but got {result}"

    # Ensure that a warning was logged
    assert "The book catalog is empty." in caplog.text, "Expected warning about empty catalog not found in logs."

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, author, title, year, genre FROM books WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_all_books_ordered_by_author(mock_cursor):
    """Test retrieving all books ordered by play count."""

    # Simulate that there are multiple books in the database
    mock_cursor.fetchall.return_value = [
        (2, "George Orwell", "1984", 1949, "Science Fiction"),
        (1, "Harper Lee", "To Kill a Mockingbird", 1960, "Novel"),
        (3, "J.D. Salinger", "The Catcher in the Rye", 1951, "Novel")
    ]

    # Call the get_all_books function with sort_by_author = True
    books = get_all_books(sort_by_author=True)

    # Ensure the results are sorted by play count
    expected_result = [
        {"id": 2, "author": "George Orwell", "title": "1984", "year": 1949, "genre": "Science Fiction"},
        {"id": 1, "author": "Harper Lee", "title": "To Kill a Mockingbird", "year": 1960, "genre": "Novel"},
        {"id": 3, "author": "J.D. Salinger", "title": "The Catcher in the Rye", "year": 1951, "genre": "Novel"}
    ]

    assert books == expected_result, f"Expected {expected_result}, but got {books}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, author, title, year, genre
        FROM books
        WHERE deleted = FALSE
        ORDER BY author DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_book(mock_cursor, mocker):
    """Test retrieving a random book from the catalog."""

    # Simulate that there are multiple books in the database
    mock_cursor.fetchall.return_value = [
        (1, "Harper Lee", "To Kill a Mockingbird", 1960, "Novel"),
        (2, "George Orwell", "1984", 1949, "Science Fiction"),
        (3, "J.D. Salinger", "The Catcher in the Rye", 1951, "Novel")
    ]

    # Mock random number generation to return the 2nd book
    mock_random = mocker.patch("book_collection.models.book_model.get_random", return_value=2)

    # Call the get_random_book method
    result = get_random_book()

    # Expected result based on the mock random number and fetchall return value
    expected_result = Book(2, "George Orwell", "1984", 1949, "Science Fiction")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure that the random number was called with the correct number of books
    mock_random.assert_called_once_with(3)

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, author, title, year, genre FROM books WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_book_empty_catalog(mock_cursor, mocker):
    """Test retrieving a random book when the catalog is empty."""

    # Simulate that the catalog is empty
    mock_cursor.fetchall.return_value = []

    # Expect a ValueError to be raised when calling get_random_book with an empty catalog
    with pytest.raises(ValueError, match="The book catalog is empty"):
        get_random_book()

    # Ensure that the random number was not called since there are no books
    mocker.patch("book_collection.models.book_model.get_random").assert_not_called()

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, author, title, year, genre FROM books WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."