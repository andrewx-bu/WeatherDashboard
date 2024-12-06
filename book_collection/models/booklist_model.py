import logging
from typing import List
from book_collection.models.book_model import Book, update_book_count
from book_collection.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class BooklistModel:
    """
    A class to manage a booklist of books.

    Attributes:
        current_track_number (int): The current track number being played.
        booklist (List[Books]): The list of books in the booklist.

    """

    def __init__(self):
        """
        Initializes the BooklistModel with an empty booklist and the current track set to 1.
        """
        self.current_track_number = 1
        self.booklist: List[Books] = []

    ##################################################
    # Book Management Functions
    ##################################################

    def add_book_to_booklist(self, book: Books) -> None:
        """
        Adds a book to the booklist.

        Args:
            book (Books): the book to add to the booklist.

        Raises:
            TypeError: If the book is not a valid Book instance.
            ValueError: If a book with the same 'id' already exists.
        """
        logger.info("Adding new book to booklist")
        if not isinstance(book, Books):
            logger.error("Book is not a valid book")
            raise TypeError("Book is not a valid book")

        book_id = self.validate_book_id(book.id, check_in_booklist=False)
        if book_id in [book_in_booklist.id for book_in_booklist in self.booklist]:
            logger.error("Book with ID %d already exists in the booklist", book.id)
            raise ValueError(f"Book with ID {book.id} already exists in the booklist")

        self.booklist.append(book)

    def remove_book_by_book_id(self, book_id: int) -> None:
        """
        Removes a book from the booklist by its book ID.

        Args:
            book_id (int): The ID of the book to remove from the booklist.

        Raises:
            ValueError: If the booklist is empty or the book ID is invalid.
        """
        logger.info("Removing book with id %d from booklist", book_id)
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        self.booklist = [book_in_booklist for book_in_booklist in self.booklist if book_in_booklist.id != book_id]
        logger.info("Book with id %d has been removed", book_id)

    def remove_book_by_track_number(self, track_number: int) -> None:
        """
        Removes a book from the bookist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the book to remove.

        Raises:
            ValueError: If the booklist is empty or the track number is invalid.
        """
        logger.info("Removing book at track number %d from booklist", track_number)
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        booklist_index = track_number - 1
        logger.info("Removing book: %s", self.booklist[booklist_index].title)
        del self.booklist[booklist_index]

    def clear_booklist(self) -> None:
        """
        Clears all books from the booklist. If the booklist is already empty, logs a warning.
        """
        logger.info("Clearing booklist")
        if self.get_booklist_length() == 0:
            logger.warning("Clearing an empty booklist")
        self.booklist.clear()

    ##################################################
    # Booklist Retrieval Functions
    ##################################################

    def get_all_books(self) -> List[Books]:
        """
        Returns a list of all books in the booklist.
        """
        self.check_if_empty()
        logger.info("Getting all books in the bookist")
        return self.booklist

    def get_book_by_book_id(self, book_id: int) -> Books:
        """
        Retrieves a book from the booklist by its book ID.

        Args:
            book_id (int): The ID of the book to retrieve.

        Raises:
            ValueError: If the booklist is empty or the book is not found.
        """
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        logger.info("Getting book with id %d from booklist", book_id)
        return next((book for book in self.booklist if book.id == book_id), None)

    def get_book_by_track_number(self, track_number: int) -> Books:
        """
        Retrieves a book from the booklist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the book to retrieve.

        Raises:
            ValueError: If the booklist is empty or the track number is invalid.
        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        booklist_index = track_number - 1
        logger.info("Getting book at track number %d from booklist", track_number)
        return self.booklist[booklist_index]

    def get_current_book(self) -> Books:
        """
        Returns the current book being played.
        """
        self.check_if_empty()
        return self.get_book_by_track_number(self.current_track_number)

    def get_booklist_length(self) -> int:
        """
        Returns the number of books in the booklist.
        """
        return len(self.booklist)

    def get_booklist_duration(self) -> int:
        """
        Returns the total duration of the booklist in seconds.
        """
        return sum(book.duration for book in self.booklist)

    ##################################################
    # Bookist Movement Functions
    ##################################################

    def go_to_track_number(self, track_number: int) -> None:
        """
        Sets the current track number to the specified track number.

        Args:
            track_number (int): The track number to set as the current track.
        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        logger.info("Setting current track number to %d", track_number)
        self.current_track_number = track_number

    def move_book_to_beginning(self, book_id: int) -> None:
        """
        Moves a book to the beginning of the booklist.

        Args:
            book_id (int): The ID of the book  to move to the beginning.
        """
        logger.info("Moving book with ID %d to the beginning of the booklist", book_id)
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        book = self.get_book_by_book_id(book_id)
        self.booklist.remove(book)
        self.booklist.insert(0, book)
        logger.info("Book with ID %d has been moved to the beginning", book_id)

    def move_book_to_end(self, book_id: int) -> None:
        """
        Moves a book to the end of the booklist.

        Args:
            book_id (int): The ID of the book to move to the end.
        """
        logger.info("Moving book with ID %d to the end of the booklist", book_id)
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        book = self.get_book_by_book_id(book_id)
        self.booklist.remove(book)
        self.booklist.append(book)
        logger.info("Book with ID %d has been moved to the end", book_id)

    def move_book_to_track_number(self, book_id: int, track_number: int) -> None:
        """
        Moves a book to a specific track number in the booklist.

        Args:
            book_id (int): The ID of the book to move.
            track_number (int): The track number to move the book to (1-indexed).
        """
        logger.info("Moving book with ID %d to track number %d", book_id, track_number)
        self.check_if_empty()
        book_id = self.validate_book_id(book_id)
        track_number = self.validate_track_number(track_number)
        booklist_index = track_number - 1
        book= self.get_book_by_book_id(book_id)
        self.booklist.remove(book)
        self.booklist.insert(booklist_index, book)
        logger.info("Book with ID %d has been moved to track number %d", book_id, track_number)

    def swap_books_in_booklist(self, book1_id: int, book2_id: int) -> None:
        """
        Swaps the positions of two books in the booklist.

        Args:
            book1_id (int): The ID of the first book to swap.
            book2_id (int): The ID of the second book to swap.

        Raises:
            ValueError: If you attempt to swap a book with itself.
        """
        logger.info("Swapping books with IDs %d and %d", book1_id, book2_id)
        self.check_if_empty()
        book1_id = self.validate_book_id(book1_id)
        book2_id = self.validate_book_id(book2_id)

        if book1_id == book2_id:
            logger.error("Cannot swap a book with itself, both book IDs are the same: %d", book1_id)
            raise ValueError(f"Cannot swap a book with itself, both book IDs are the same: {book1_id}")

        book1 = self.get_book_by_book_id(book1_id)
        book2 = self.get_book_by_book_id(book2_id)
        index1 = self.booklist.index(book1)
        index2 = self.booklist.index(book2)
        self.booklist[index1], self.booklist[index2] = self.booklist[index2], self.booklist[index1]
        logger.info("Swapped books with IDs %d and %d", book1_id, book2_id)

    ##################################################
    # Booklist Playback Functions
    ##################################################

    def play_current_book(self) -> None:
        """
        Plays the current book.

        Side-effects:
            Updates the current track number.
            Updates the book count for the book.
        """
        self.check_if_empty()
        current_book = self.get_book_by_track_number(self.current_track_number)
        logger.info("Playing book: %s (ID: %d) at track number: %d", current_book.title, current_book.id, self.current_track_number)
        update_book_count(current_book.id)
        logger.info("Updated book count for book: %s (ID: %d)", current_book.title, current_book.id)
        previous_track_number = self.current_track_number
        self.current_track_number = (self.current_track_number % self.get_booklist_length()) + 1
        logger.info("Track number updated from %d to %d", previous_track_number, self.current_track_number)

    def play_entire_booklist(self) -> None:
        """
        Plays the entire booklist.

        Side-effects:
            Resets the current track number to 1.
            Updates the book count for each book.
        """
        self.check_if_empty()
        logger.info("Starting to play the entire booklist.")
        self.current_track_number = 1
        logger.info("Reset current track number to 1.")
        for _ in range(self.get_booklist_length()):
            logger.info("Playing track number: %d", self.current_track_number)
            self.play_current_book()
        logger.info("Finished playing the entire booklist. Current track number reset to 1.")

    def play_rest_of_booklist(self) -> None:
        """
        Plays the rest of the booklist from the current track.

        Side-effects:
            Updates the current track number back to 1.
            Updates the play count for each book in the rest of the book list.
        """
        self.check_if_empty()
        logger.info("Starting to play the rest of the booklist from track number: %d", self.current_track_number)
        for _ in range(self.get_booklist_length() - self.current_track_number + 1):
            logger.info("Playing track number: %d", self.current_track_number)
            self.play_current_book()
        logger.info("Finished playing the rest of the booklist. Current track number reset to 1.")

    def rewind_booklist(self) -> None:
        """
        Rewinds the booklist to the beginning.
        """
        self.check_if_empty()
        logger.info("Rewinding booklist to the beginning.")
        self.current_track_number = 1

    ##################################################
    # Utility Functions
    ##################################################

    def validate_book_id(self, book_id: int, check_in_booklist: bool = True) -> int:
        """
        Validates the given book ID, ensuring it is a non-negative integer.

        Args:
            book_id (int): The book ID to validate.
            check_in_booklist (bool, optional): If True, checks if the book  ID exists in the booklist.
                                                If False, skips the check. Defaults to True.

        Raises:
            ValueError: If the book ID is not a valid non-negative integer.
        """
        try:
            book_id = int(book_id)
            if book_id < 0:
                logger.error("Invalid book id %d", book_id)
                raise ValueError(f"Invalid book id: {book_id}")
        except ValueError:
            logger.error("Invalid book id %s", book_id)
            raise ValueError(f"Invalid book id: {book_id}")

        if check_in_booklist:
            if book_id not in [book_in_booklist.id for book_in_booklist in self.booklist]:
                logger.error("Book with id %d not found in booklist", book_id)
                raise ValueError(f"Book with id {book_id} not found in booklist")

        return book_id

    def validate_track_number(self, track_number: int) -> int:
        """
        Validates the given track number, ensuring it is a non-negative integer within the booklist's range.

        Args:
            track_number (int): The track number to validate.

        Raises:
            ValueError: If the track number is not a valid non-negative integer or is out of range.
        """
        try:
            track_number = int(track_number)
            if track_number < 1 or track_number > self.get_booklist_length():
                logger.error("Invalid track number %d", track_number)
                raise ValueError(f"Invalid track number: {track_number}")
        except ValueError:
            logger.error("Invalid track number %s", track_number)
            raise ValueError(f"Invalid track number: {track_number}")

        return track_number

    def check_if_empty(self) -> None:
        """
        Checks if the booklist is empty, logs an error, and raises a ValueError if it is.

        Raises:
            ValueError: If the booklist is empty.
        """
        if not self.booklist:
            logger.error("Booklist is empty")
            raise ValueError("Booklist is empty")
