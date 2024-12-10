import pytest
from unittest.mock import MagicMock
from models.FavoriteModel import FavoriteModel
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
    mocker.patch("models.FavoriteModel.get_db_connection", return_value=mock_conn)

    return mock_cursor  # Return the mock cursor for test assertions

# Add, remove, update favorite

def test_add_favorite_success(mock_cursor):
    """Test adding a favorite location when it does not already exist."""
    user_id = 9999
    location = "ASd"

    FavoriteModel.add_favorite(user_id, location)

    # Verify the insert SQL query was executed
    if mock_cursor.execute.call_args:
        executed_query, query_params = mock_cursor.execute.call_args[0]
        assert executed_query == "INSERT INTO favorites (user_id, location) VALUES (?, ?)"
        assert query_params == (user_id, location)

def test_remove_favorite_success(mock_cursor):
    """Test removing an existing favorite location."""
    user_id = 9999
    location = "New York"

    # Simulate that the location exists for the user
    mock_cursor.fetchone.return_value = (1,)

    FavoriteModel.remove_favorite(user_id, location)

    # Verify the delete SQL query was executed
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "DELETE FROM favorites WHERE user_id = ? AND location = ?"
    assert query_params == (user_id, location)

def test_remove_favorite_not_found(mock_cursor):
    """Test trying to remove a favorite location that doesn't exist."""
    user_id = 9999
    location = "Nonexistent Location"

    # Simulate that the location does not exist for the user
    mock_cursor.fetchone.return_value = None  # No existing favorite
    with pytest.raises(ValueError, match=f"'{location}' is not a favorite location for this user."):
        FavoriteModel.remove_favorite(user_id, location)

def test_update_favorite_success(mock_cursor):
    """Test updating a favorite location."""
    user_id = 9999
    old_location = "Old Location"
    new_location = "New Location"

    # Simulate that the old location exists and the new location doesn't exist
    mock_cursor.fetchone.side_effect = [(1,), None]  # old location exists, new doesn't

    # Call the function to update the favorite
    FavoriteModel.update_favorite(user_id, old_location, new_location)

    # Verify the update SQL query was executed
    executed_query, query_params = mock_cursor.execute.call_args_list[-1][0]
    expected_query = '''
            UPDATE favorites SET location = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND location = ?
    '''.strip()
    assert executed_query.strip() == expected_query
    assert query_params == (new_location, user_id, old_location)

# Clear favorites

def test_clear_favorites(mock_cursor):
    """Test clearing all favorite locations for a user."""
    user_id = 9999

    # Call the function to clear all favorites
    FavoriteModel.clear_favorites(user_id)

    # Verify the delete SQL query was executed
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "DELETE FROM favorites WHERE user_id = ?"
    assert query_params == (user_id,)

# Get favorites

def test_get_favorites_success(mock_cursor):
    """Test successfully fetching a list of favorites for a user."""
    user_id = 1
    # Simulate some favorites data being fetched from the database
    mock_cursor.fetchall.return_value = [
        (1, "New York", "2024-01-01 12:00:00", "2024-01-02 12:00:00"),
        (2, "Los Angeles", "2024-01-05 12:00:00", "2024-01-06 12:00:00")
    ]

    result = FavoriteModel.get_favorites(user_id)
    expected = [
        (1, "New York", "2024-01-01 12:00:00", "2024-01-02 12:00:00"),
        (2, "Los Angeles", "2024-01-05 12:00:00", "2024-01-06 12:00:00")
    ]
    assert result == expected, f"Expected {expected}, but got {result}"

def test_get_favorites_no_data(mock_cursor):
    """Test when no favorites are found for a user."""
    user_id = 2
    # Simulate no favorites being fetched from the database
    mock_cursor.fetchall.return_value = []
    
    result = FavoriteModel.get_favorites(user_id)
    assert result == [], f"Expected [], but got {result}"