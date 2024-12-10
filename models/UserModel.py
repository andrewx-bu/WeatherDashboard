import bcrypt
import sqlite3
from models.User import User
from utils.logger import setup_logger
from utils.sql import get_db_connection

logger = setup_logger()

class UserModel:
    @staticmethod
    def create_user(username, password):
        """
        Creates a new user in the database with the given username and password.
        The password is hashed before being stored.

        Args:
            username (str): The username of the user to be created.
            password (str): The password of the user to be created.

        Raises:
            sqlite3.Error: For general database errors.
        """
        if not username or not password:
            raise Exception(f"Invalid input: username and password are required")
        try:
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)',
                (username, salt.decode(), password_hash.decode())
            )
            conn.commit()
            conn.close()
            logger.info(f"User '{username}' created successfully.")
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error creating user '{username}': {e}")
            raise sqlite3.IntegrityError(f"User '{username}' already exists: {str(e)}")
        except sqlite3.Error as e:
            logger.error(f"SQLite error creating user '{username}': {e}")
            raise sqlite3.Error(f"Error creating user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating user '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def delete_user(username):
        """
        Deletes a user from the database by username.

        Args:
            username (str): The username of the user to be deleted.

        Raises:
            sqlite3.Error: For general database errors.
        """
        if not username:
            raise Exception(f"Invalid input: username is required")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            conn.close()
            logger.info(f"User '{username}' deleted successfully.")
        except sqlite3.Error as e:
            logger.error(f"SQLite error deleting user '{username}': {e}")
            raise sqlite3.Error(f"Error deleting user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting user '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_user_by_id(user_id):
        """
        Gets a user by their ID.

        Args:
            user_id (int): The unique ID of the user to be retrieved.

        Returns:
            User: Returns a User object if found, otherwise None.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, salt, password_hash FROM users WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                return User(*user_data)
            return None
        except sqlite3.Error as e:
            logger.error(f"SQLite error retrieving user by ID '{user_id}': {e}")
            raise sqlite3.Error(f"Error retrieving user by ID: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving user by ID '{user_id}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_user_by_username(username):
        """
        Gets a user by their username.

        Args:
            username (str): The username of the user to be retrieved.

        Returns:
            User: Returns a User object if found, otherwise None.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, salt, password_hash FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                return User(*user_data)
            return None
        except sqlite3.Error as e:
            logger.error(f"SQLite error retrieving user by username '{username}': {e}")
            raise sqlite3.Error(f"Error retrieving user by username: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving user by username '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_all_users():
        """
        Retrieves all users from the database.

        Returns:
            List[User]: A list of User objects.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, salt, password_hash FROM users')
            users_data = cursor.fetchall()
            conn.close()
            return [User(*user_data).to_dict() for user_data in users_data]
        except sqlite3.Error as e:
            logger.error(f"SQLite error retrieving all users: {e}")
            raise sqlite3.Error(f"Error retrieving all users: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving all users: {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    @staticmethod
    def update_password(username, new_password):
        """
        Updates the password for a user. Hashes the new password before storing it.

        Args:
            username (str): The username of the user whose password will be updated.
            new_password (str): The new password to be set for the user.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET salt = ?, password_hash = ? WHERE username = ?',
                (salt.decode(), password_hash.decode(), username)
            )
            conn.commit()
            conn.close()
            logger.info(f"Password for user '{username}' updated successfully.")
        except sqlite3.Error as e:
            logger.error(f"SQLite error updating password for user '{username}': {e}")
            raise sqlite3.Error(f"Error updating password: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating password for user '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Verifies the user's credentials by comparing the provided password with the stored hash.

        Args:
            username (str): The username of the user attempting to authenticate.
            password (str): The password provided by the user to authenticate.

        Returns:
            bool: True if the credentials are valid, otherwise False.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()

            if user:
                password_hash = user[1]
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    return True
            return False
        except sqlite3.Error as e:
            logger.error(f"SQLite error authenticating user '{username}': {e}")
            raise sqlite3.Error(f"Error authenticating user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error authenticating user '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def is_username_taken(username):
        """
        Checks if the given username is already taken by another user.

        Args:
            username (str): The username to be checked.

        Returns:
            bool: True if the username exists, otherwise False.

        Raises:
            sqlite3.Error: For general database errors.
        """
        try:
            user = UserModel.get_user_by_username(username)
            return user is not None
        except sqlite3.Error as e:
            logger.error(f"SQLite error checking if username '{username}' is taken: {e}")
            raise sqlite3.Error(f"Error checking username availability: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking username '{username}': {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    @staticmethod
    def check_password_validity(password):
        """
        Checks if the password meets the required complexity standards.

        Args:
            password (str): The password to be checked.

        Returns:
            bool: True if the password meets complexity requirements, otherwise False.
        """
        if len(password) < 8 or len(password) > 20:  # Password must be between 8 and 20 characters long
            return False
        if not any(char.isdigit() for char in password):  # Must contain at least one digit
            return False
        if not any(char.isalpha() for char in password):  # Must contain at least one letter
            return False
        return True
