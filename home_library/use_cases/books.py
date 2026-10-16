from home_library.domain import Book, BookDraft
from home_library.persistence import books as book_store
from home_library.persistence.errors import DuplicateISBNRecord


class BookNotFound(Exception):
    pass


class DuplicateISBN(Exception):
    pass


def get_books(unit_of_work, search="") -> list[Book]:
    return book_store.find_books(unit_of_work, search.strip())


def find_book(unit_of_work, book_id: int) -> Book | None:
    return book_store.find_book(unit_of_work, book_id)


def find_isbn_conflict(unit_of_work, isbn: str | None, exclude_id=None) -> bool:
    if isbn is None:
        return False
    return book_store.isbn_exists(unit_of_work, isbn, exclude_id)


def create_book(unit_of_work, draft: BookDraft) -> Book:
    if find_isbn_conflict(unit_of_work, draft.isbn):
        raise DuplicateISBN("That ISBN is already in your collection.")
    try:
        return book_store.insert_book(unit_of_work, draft)
    except DuplicateISBNRecord as error:
        raise DuplicateISBN("That ISBN is already in your collection.") from error


def update_book(unit_of_work, book_id: int, draft: BookDraft) -> Book:
    if find_isbn_conflict(unit_of_work, draft.isbn, book_id):
        raise DuplicateISBN("That ISBN is already in your collection.")
    try:
        book = book_store.update_book(unit_of_work, book_id, draft)
    except DuplicateISBNRecord as error:
        raise DuplicateISBN("That ISBN is already in your collection.") from error
    if book is None:
        raise BookNotFound(f"Book {book_id} was not found.")
    return book


def delete_book(unit_of_work, book_id: int) -> None:
    if not book_store.delete_book(unit_of_work, book_id):
        raise BookNotFound(f"Book {book_id} was not found.")
