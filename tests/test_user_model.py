import pytest
import bcrypt
import sqlite3
from unittest.mock import MagicMock
from models.UserModel import UserModel
from utils.logger import setup_logger

logger = setup_logger()

@pytest.fixture
def mock_cursor(mocker):
    # Create a mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure the mock cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None
    mock_conn.close.return_value = None

    # Patch the `get_db_connection` to return the mock connection
    mocker.patch("models.UserModel.get_db_connection", return_value=mock_conn)

    return mock_cursor  # Return the mock cursor for test assertions

# Create User

def test_create_user_success(mock_cursor):
    """Test successful user creation."""
    username = "test_user"
    password = "password123"

    # Call the function
    UserModel.create_user(username, password)

    # Verify SQL execution
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)"
    assert query_params[0] == username
    assert bcrypt.checkpw(password.encode('utf-8'), query_params[2].encode('utf-8'))

def test_create_user_duplicate_username(mock_cursor):
    """Test handling of duplicate username."""
    username = "existing_user"
    password = "password123"

    # Simulate duplicate username error
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: users.username")

    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed: users.username"):
        UserModel.create_user(username, password)

def test_create_user_db_error(mock_cursor):
    """Test handling of general database errors."""
    username = "test_user"
    password = "password123"

    # Simulate general database error
    mock_cursor.execute.side_effect = sqlite3.Error("General database error")

    with pytest.raises(sqlite3.Error, match="General database error"):
        UserModel.create_user(username, password)

def test_create_user_invalid_username(mock_cursor):
    """Test creating a user with an invalid username."""
    password = "password123"

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(None, password)

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user("", password)

def test_create_user_invalid_password(mock_cursor):
    """Test creating a user with an invalid password."""
    username = "test_user"

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(username, None)

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(username, "")

def test_create_user_unexpected_error(mocker, mock_cursor):
    """Test unexpected error during user creation."""
    username = "test_user"
    password = "password123"

    # Simulate unexpected error
    mock_cursor.execute.side_effect = ValueError("Unexpected error occurred")

    with pytest.raises(Exception, match="Unexpected error: Unexpected error occurred"):
        UserModel.create_user(username, password)

# Delete User

def test_delete_user_success(mock_cursor):
    """Test successful deletion of a user."""
    username = "test_user"
    
    UserModel.delete_user(username)
    
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "DELETE FROM users WHERE username = ?"
    assert query_params[0] == username

def test_delete_user_non_existing(mock_cursor):
    """Test attempting to delete a user who does not exist."""
    username = "non_existing_user"
    
    # Simulate no rows being deleted
    mock_cursor.rowcount = 0

    # Call the function to delete the user
    UserModel.delete_user(username)
    
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "DELETE FROM users WHERE username = ?"
    assert query_params[0] == username

def test_delete_user_db_error(mock_cursor):
    """Test handling of general database errors."""
    username = "test_user"
    
    # Simulate general databse error
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    
    with pytest.raises(sqlite3.Error, match="Error deleting user: SQLite error occurred"):
        UserModel.delete_user(username)

def test_delete_user_invalid_username(mock_cursor):
    """Test attempting to delete a user with invalid username."""
    
    # Simulate invalid usernames (None or empty string)
    invalid_usernames = [None, ""]
    
    for username in invalid_usernames:
        # Expect an exception to be raised for invalid username
        with pytest.raises(Exception, match="Invalid input: username is required"):
            UserModel.delete_user(username)

def test_delete_user_unexpected_error(mock_cursor):
    """Test handling of an unexpected error during user deletion."""
    username = "test_user"
    
    # Simulate an unexpected error (e.g., ZeroDivisionError)
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    
    # Verify that the error is raised and the correct exception is handled
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.delete_user(username)