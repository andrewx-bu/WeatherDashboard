import pytest
import sqlite3
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

# Test successful addition of a favorite
def test_add_favorite_success(mock_cursor):
    """Test adding a favorite location when it does not already exist."""
    user_id = 9999
    location = "New York"

    # Simulate that the location does not already exist for the user
    mock_cursor.fetchone.return_value = None  # No existing favorite

    # Call the function to add a favorite
    FavoriteModel.add_favorite(user_id, location)

    # Verify the insert SQL query was executed
    executed_query, query_params = mock_cursor.execute.call_args[0]
    assert executed_query == "INSERT INTO favorites (user_id, location) VALUES (?, ?)"
    assert query_params == (user_id, location)

    # Verify the commit was called to save changes
    mock_cursor.commit.assert_called_once()

