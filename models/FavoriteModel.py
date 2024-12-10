from utils.logger import setup_logger
from utils.sql import get_db_connection

logger = setup_logger()

class FavoriteModel:
    @staticmethod
    def add_favorite(user_id, location):
        """
        Add a favorite location for a user.
        
        Args:
            user_id (int): The ID of the user.
            location (str): The location to be added as a favorite.

        Raises:
            ValueError: If the location is already a favorite for this user.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the location already exists for the user
            cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))
            existing_favorite = cursor.fetchone()

            if existing_favorite:
                logger.warning(f"Favorite location '{location}' already exists for user {user_id}.")
                raise ValueError(f"'{location}' is already a favorite location for this user.")

            cursor.execute(
                'INSERT INTO favorites (user_id, location) VALUES (?, ?)', 
                (user_id, location)
            )
            logger.info(f"User {user_id} added new favorite location: {location}")
            conn.commit()

    @staticmethod
    def remove_favorite(user_id, location):
        """
        Remove a favorite location for a user.
        
        Args:
            user_id (int): The ID of the user.
            location (str): The location to be removed from the favorites.

        Raises:
            ValueError: If the location is not a favorite for this user.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the location exists for the user
        cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))
        favorite = cursor.fetchone()
        
        if not favorite:
            logger.warning(f"User {user_id} tried to remove a non-existing favorite: {location}")
            conn.close()
            raise ValueError(f"'{location}' is not a favorite location for this user.")
        
        cursor.execute('DELETE FROM favorites WHERE user_id = ? AND location = ?', (user_id, location))
        conn.commit()
        logger.info(f"User {user_id} removed favorite location: {location}")
        conn.close()

    @staticmethod
    def update_favorite(user_id, old_location, new_location):
        """
        Update a user's favorite location.
        
        Args:
            user_id (int): The ID of the user.
            old_location (str): The location to be replaced.
            new_location (str): The new location to replace the old one.

        Raises:
            ValueError: If the new location is already a favorite or if the old location is not a favorite.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the new location already exists for the user
        cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND location = ?', (user_id, new_location))
        existing_favorite = cursor.fetchone()
        
        if existing_favorite:
            logger.warning(f"User {user_id} tried to add an already existing favorite: {new_location}")
            conn.close()
            raise ValueError(f"'{new_location}' is already a favorite location for this user.")
        
        cursor.execute('''
            UPDATE favorites SET location = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND location = ?
        ''', (new_location, user_id, old_location))

        if cursor.rowcount == 0:
            logger.warning(f"User {user_id} tried to update a non-existing favorite: {old_location}")
            conn.close()
            raise ValueError(f"'{old_location}' is not a favorite location for this user.")

        conn.commit()
        logger.info(f"User {user_id} updated favorite location '{old_location}' to '{new_location}'")
        conn.close()

    @staticmethod
    def clear_favorites(user_id):
        """
        Clear all favorite locations for a user.
        
        Args:
            user_id (int): The ID of the user.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        conn.commit()
        logger.info(f"User {user_id} cleared all favorite locations.")
        conn.close()

    @staticmethod
    def get_favorites(user_id):
        """
        Get all favorite locations for a user.
        
        Args:
            user_id (int): The ID of the user.

        Returns:
            List: A list of tuples representing the user's favorite locations.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, location, created_at, updated_at FROM favorites WHERE user_id = ?', (user_id,))
        favorites = cursor.fetchall()
        conn.close()
        logger.info(f"Fetched {len(favorites)} favorite(s) for user {user_id}.")
        return favorites