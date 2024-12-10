import pytest
import bcrypt
import sqlite3
from unittest.mock import MagicMock
from models.User import User
from models.UserModel import UserModel

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

# User to dict

def test_user_to_dict():
    """Test the to_dict method of the User class."""
    user = User(id=1, username="test_user", password_hash="hashed_password", salt="salt")
    
    # Expected dictionary representation
    expected_dict = {
        'id': 1,
        'username': "test_user",
    }
    
    result = user.to_dict()
    assert result == expected_dict, "The to_dict method did not return the expected dictionary."

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

def test_create_user_invalid_username():
    """Test creating a user with an invalid username."""
    password = "password123"

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(None, password)

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user("", password)

def test_create_user_invalid_password():
    """Test creating a user with an invalid password."""
    username = "test_user"

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(username, None)

    with pytest.raises(Exception, match="Invalid input: username and password are required"):
        UserModel.create_user(username, "")

def test_create_user_unexpected_error(mock_cursor):
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

def test_delete_user_invalid_username():
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

# Get User

def test_get_user_by_id_success(mock_cursor):
    """Test getting a user by ID successfully."""
    user_id = 1
    expected_user = User(id=user_id, username="test_user", password_hash="hashed_password", salt="salt")

    # Simulate the return value of the cursor to match a user with this ID
    mock_cursor.fetchone.return_value = (user_id, "test_user", "hashed_password", "salt")
    
    user = UserModel.get_user_by_id(user_id)
    
    assert user.id == expected_user.id
    assert user.username == expected_user.username

def test_get_user_by_id_not_found(mock_cursor):
    """Test that getting a user by ID returns None if no user is found."""
    user_id = 9992
    
    mock_cursor.fetchone.return_value = None
    user = UserModel.get_user_by_id(user_id)
    
    assert user is None

def test_get_user_by_id_db_error(mock_cursor):
    """Test handling of general databse errors while retrieving user by ID."""
    user_id = 1
    
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error retrieving user by ID: SQLite error occurred"):
        UserModel.get_user_by_id(user_id)

def test_get_user_by_id_unexpected_error(mock_cursor):
    """Test handling of an unexpected error while retrieving user by ID."""
    user_id = 1
    
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.get_user_by_id(user_id)

def test_get_user_by_username_success(mock_cursor):
    """Test getting a user by username successfully."""
    username = "test_user"
    expected_user = User(id=1, username=username, password_hash="hashed_password", salt ="salt")

    mock_cursor.fetchone.return_value = (1, username, "hashed_password", "salt")
    user = UserModel.get_user_by_username(username)
    
    # Verify that the returned user is correct
    assert user.username == expected_user.username
    assert user.id == expected_user.id

def test_get_user_by_username_not_found(mock_cursor):
    """Test that getting a user by username returns None if no user is found."""
    username = "non_existing_user"
    
    mock_cursor.fetchone.return_value = None
    user = UserModel.get_user_by_username(username)
    
    assert user is None

def test_get_user_by_username_db_error(mock_cursor):
    """Test handling of general databse errors while retrieving user by username."""
    username = "test_user"
    
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error retrieving user by username: SQLite error occurred"):
        UserModel.get_user_by_username(username)

def test_get_user_by_username_unexpected_error(mock_cursor):
    """Test handling of an unexpected error while retrieving user by username."""
    username = "test_user"
    
    # Simulate an unexpected error
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.get_user_by_username(username)

def test_get_all_users_success(mock_cursor):
    """Test getting all users successfully."""
    mock_cursor.fetchall.return_value = [
        (1, "user1", "hashed_password1", "salt1"),
        (2, "user2", "hashed_password2", "salt2")
    ]
    
    users = UserModel.get_all_users()
    
    # Verify that two users are returned
    assert len(users) == 2
    assert users[0]["username"] == "user1"
    assert users[1]["username"] == "user2"

def test_get_all_users_empty(mock_cursor):
    """Test that getting all users returns an empty list if no users are found."""
    mock_cursor.fetchall.return_value = []
    
    users = UserModel.get_all_users()
    assert len(users) == 0

def test_get_all_users_db_error(mock_cursor):
    """Test handling of db error while retrieving all users."""
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error retrieving all users: SQLite error occurred"):
        UserModel.get_all_users()

def test_get_all_users_unexpected_error(mock_cursor):
    """Test handling of an unexpected error while retrieving all users."""
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.get_all_users()

# Other Functions

def test_update_password_success(mock_cursor):
    """Test successful password update."""
    username = "test_user"
    new_password = "newpassword123"

    UserModel.update_password(username, new_password)
    
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == 'UPDATE users SET salt = ?, password_hash = ? WHERE username = ?'
    
    # Check if the salt and hashed password are generated and passed to the query
    salt = query_params[0]
    password_hash = query_params[1]
    
    # Ensure the password is hashed and salted
    assert bcrypt.checkpw(new_password.encode('utf-8'), password_hash.encode('utf-8'))
    # Check that the username is passed correctly
    assert query_params[2] == username

def test_update_password_db_error(mock_cursor):
    """Test handling of db errors during password update."""
    username = "test_user"
    new_password = "newpassword123"
    
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error updating password: SQLite error occurred"):
        UserModel.update_password(username, new_password)

def test_update_password_unexpected_error(mock_cursor):
    """Test handling of an unexpected error during password update."""
    username = "test_user"
    new_password = "newpassword123"
    
    # Simulate an unexpected error during the password update
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.update_password(username, new_password)

def test_authenticate_user_success(mock_cursor):
    """Test successful user authentication."""
    username = "test_user"
    correct_password = "correctpassword"
    hashed_password = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode()
    
    # Simulate the retrieval of a user with the correct password hash
    mock_cursor.fetchone.return_value = (1, hashed_password)
    
    result = UserModel.authenticate_user(username, correct_password)
    assert result is True

def test_authenticate_user_invalid_password(mock_cursor):
    """Test unsuccessful user authentication due to invalid password."""
    username = "test_user"
    incorrect_password = "wrongpassword"
    hashed_password = bcrypt.hashpw("correctpassword".encode('utf-8'), bcrypt.gensalt()).decode()
    
    # Simulate the retrieval of a user with the correct password hash
    mock_cursor.fetchone.return_value = (1, hashed_password)

    result = UserModel.authenticate_user(username, incorrect_password)
    assert result is False

def test_authenticate_user_not_found(mock_cursor):
    """Test that authentication fails if user is not found."""
    username = "nonexistent_user"
    
    # Simulate no user found
    mock_cursor.fetchone.return_value = None
    
    result = UserModel.authenticate_user(username, "password123")
    assert result is False

def test_authenticate_user_db_error(mock_cursor):
    """Test handling of db errors during user authentication."""
    username = "test_user"
    password = "password123"
    
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error authenticating user: SQLite error occurred"):
        UserModel.authenticate_user(username, password)

def test_authenticate_user_unexpected_error(mock_cursor):
    """Test handling of an unexpected error during user authentication."""
    username = "test_user"
    password = "password123"
    
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.authenticate_user(username, password)

def test_is_username_taken_true(mock_cursor):
    """Test when the username is already taken."""
    username = "test_user"
    
    mock_cursor.fetchone.return_value = (1, username, "hashed_password", "salt")
    result = UserModel.is_username_taken(username)
    assert result is True

def test_is_username_taken_false(mock_cursor):
    """Test when the username is not taken."""
    username = "test_user"
    
    mock_cursor.fetchone.return_value = None
    result = UserModel.is_username_taken(username)
    assert result is False

def test_is_username_taken_db_error(mock_cursor):
    """Test handling of db errors while checking if username is taken."""
    username = "test_user"
    
    mock_cursor.execute.side_effect = sqlite3.Error("SQLite error occurred")
    with pytest.raises(sqlite3.Error, match="Error checking username availability: Error retrieving user by username: SQLite error occurred"):
        UserModel.is_username_taken(username)

def test_is_username_taken_unexpected_error(mock_cursor):
    """Test handling of an unexpected error while checking if username is taken."""
    username = "test_user"
    
    mock_cursor.execute.side_effect = ValueError("Unexpected error")
    with pytest.raises(Exception, match="Unexpected error"):
        UserModel.is_username_taken(username)

def test_check_password_validity_valid():
    """Test valid password that meets the requirements."""
    password = "Valid123"
    
    result = UserModel.check_password_validity(password)
    assert result is True

def test_check_password_validity_too_short():
    """Test password that is too short."""
    password = "Short1"

    result = UserModel.check_password_validity(password)
    assert result is False

def test_check_password_validity_too_long():
    """Test password that is too long."""
    password = "ThisIsWayyyyyyyyTooLong123"
    
    result = UserModel.check_password_validity(password)
    assert result is False

def test_check_password_validity_missing_digit():
    """Test password missing a digit."""
    password = "NoDigitHere"
    
    result = UserModel.check_password_validity(password)
    assert result is False

def test_check_password_validity_missing_letter():
    """Test password missing a letter."""
    password = "123456789"

    result = UserModel.check_password_validity(password)
    assert result is False