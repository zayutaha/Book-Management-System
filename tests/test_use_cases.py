import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from home_library.domain import Author, AuthorBookGroup, AuthorDraft, Book, BookDraft
from home_library.persistence.errors import DuplicateAuthorRecord, DuplicateISBNRecord
from home_library.use_cases import authors as author_use_cases
from home_library.use_cases import books as book_use_cases
from home_library.use_cases.books import (
    BookNotFound,
    DuplicateISBN,
    create_book,
    delete_book,
    find_book,
    find_isbn_conflict,
    get_books,
    update_book,
)


class BookUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.uow = object()
        self.draft = BookDraft("Dune", "9780306406157", "12.50", 1)
        self.book = Book(1, "Dune", "9780306406157", Decimal("12.50"), 1, "Frank Herbert")
        self.store_patch = patch("home_library.use_cases.books.book_store")
        self.store = self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        self.author_store_patch = patch("home_library.use_cases.books.author_store")
        self.author_store = self.author_store_patch.start()
        self.author_store.author_id_exists.return_value = True
        self.addCleanup(self.author_store_patch.stop)

    def test_get_books_trims_search_before_query(self):
        self.store.find_books.return_value = [self.book]
        self.assertEqual(get_books(self.uow, "  Dune  "), [self.book])
        self.store.find_books.assert_called_once_with(self.uow, "Dune")

    def test_get_books_defaults_to_unfiltered_query(self):
        self.store.find_books.return_value = []
        self.assertEqual(get_books(self.uow), [])
        self.store.find_books.assert_called_once_with(self.uow, "")

    def test_find_book_delegates_by_id(self):
        self.store.find_book.return_value = self.book
        self.assertEqual(find_book(self.uow, 1), self.book)
        self.store.find_book.assert_called_once_with(self.uow, 1)

    def test_no_isbn_never_queries_for_conflict(self):
        self.assertFalse(find_isbn_conflict(self.uow, None))
        self.store.isbn_exists.assert_not_called()

    def test_isbn_conflict_query_passes_excluded_id(self):
        self.store.isbn_exists.return_value = True
        self.assertTrue(find_isbn_conflict(self.uow, "9780306406157", 1))
        self.store.isbn_exists.assert_called_once_with(self.uow, "9780306406157", 1)

    def test_create_book_checks_duplicate_then_inserts(self):
        self.store.isbn_exists.return_value = False
        self.store.insert_book.return_value = self.book
        self.assertEqual(create_book(self.uow, self.draft), self.book)
        self.store.insert_book.assert_called_once_with(self.uow, self.draft)
        self.author_store.author_id_exists.assert_called_once_with(self.uow, 1)

    def test_create_book_rejects_duplicate_before_insert(self):
        self.store.isbn_exists.return_value = True
        with self.assertRaises(DuplicateISBN):
            create_book(self.uow, self.draft)
        self.store.insert_book.assert_not_called()

    def test_create_book_maps_database_duplicate_race(self):
        self.store.isbn_exists.return_value = False
        self.store.insert_book.side_effect = DuplicateISBNRecord()
        with self.assertRaises(DuplicateISBN):
            create_book(self.uow, self.draft)

    def test_update_allows_keeping_same_books_isbn(self):
        self.store.isbn_exists.return_value = False
        self.store.update_book.return_value = self.book
        self.assertEqual(update_book(self.uow, 1, self.draft), self.book)
        self.store.isbn_exists.assert_called_once_with(self.uow, self.draft.isbn, 1)

    def test_update_rejects_isbn_used_by_another_book(self):
        self.store.isbn_exists.return_value = True
        with self.assertRaises(DuplicateISBN):
            update_book(self.uow, 1, self.draft)
        self.store.update_book.assert_not_called()

    def test_create_book_rejects_missing_author_before_insert(self):
        self.author_store.author_id_exists.return_value = False
        with self.assertRaises(book_use_cases.BookAuthorNotFound):
            book_use_cases.create_book(self.uow, self.draft)
        self.store.insert_book.assert_not_called()

    def test_update_maps_database_duplicate_race(self):
        self.store.isbn_exists.return_value = False
        self.store.update_book.side_effect = DuplicateISBNRecord()
        with self.assertRaises(DuplicateISBN):
            update_book(self.uow, 1, self.draft)

    def test_update_raises_not_found_when_store_returns_no_book(self):
        self.store.isbn_exists.return_value = False
        self.store.update_book.return_value = None
        with self.assertRaisesRegex(BookNotFound, "Book 7 was not found"):
            update_book(self.uow, 7, self.draft)

    def test_delete_delegates_for_existing_book(self):
        self.store.delete_book.return_value = True
        self.assertIsNone(delete_book(self.uow, 1))
        self.store.delete_book.assert_called_once_with(self.uow, 1)

    def test_delete_raises_not_found(self):
        self.store.delete_book.return_value = False
        with self.assertRaisesRegex(BookNotFound, "Book 7 was not found"):
            delete_book(self.uow, 7)


class AuthorUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.uow = object()
        self.draft = AuthorDraft("Frank Herbert", date(1920, 10, 8))
        self.author = Author(1, "Frank Herbert", date(1920, 10, 8), 2)
        self.store_patch = patch("home_library.use_cases.authors.author_store")
        self.store = self.store_patch.start()
        self.addCleanup(self.store_patch.stop)

    def test_get_authors_trims_search(self):
        self.store.find_authors.return_value = [self.author]
        self.assertEqual(author_use_cases.get_authors(self.uow, " Herbert "), [self.author])
        self.store.find_authors.assert_called_once_with(self.uow, "Herbert")

    def test_find_author_delegates_by_id(self):
        self.store.find_author.return_value = self.author
        self.assertEqual(author_use_cases.find_author(self.uow, 1), self.author)
        self.store.find_author.assert_called_once_with(self.uow, 1)

    def test_author_name_conflict_supports_excluded_author(self):
        self.store.author_name_exists.return_value = False
        self.assertFalse(author_use_cases.author_name_conflict(self.uow, "Frank Herbert", 1))
        self.store.author_name_exists.assert_called_once_with(self.uow, "Frank Herbert", 1)

    def test_create_author_checks_conflict_then_inserts(self):
        self.store.author_name_exists.return_value = False
        self.store.insert_author.return_value = self.author
        self.assertEqual(author_use_cases.create_author(self.uow, self.draft), self.author)
        self.store.insert_author.assert_called_once_with(self.uow, self.draft)

    def test_create_author_rejects_existing_name_before_insert(self):
        self.store.author_name_exists.return_value = True
        with self.assertRaises(author_use_cases.DuplicateAuthorName):
            author_use_cases.create_author(self.uow, self.draft)
        self.store.insert_author.assert_not_called()

    def test_create_author_maps_database_duplicate_race(self):
        self.store.author_name_exists.return_value = False
        self.store.insert_author.side_effect = DuplicateAuthorRecord()
        with self.assertRaises(author_use_cases.DuplicateAuthorName):
            author_use_cases.create_author(self.uow, self.draft)

    def test_update_allows_keeping_same_name_and_date(self):
        self.store.author_name_exists.return_value = False
        self.store.update_author.return_value = self.author
        self.assertEqual(author_use_cases.update_author(self.uow, 1, self.draft), self.author)
        self.store.author_name_exists.assert_called_once_with(self.uow, "Frank Herbert", 1)

    def test_update_rejects_name_used_by_another_author(self):
        self.store.author_name_exists.return_value = True
        with self.assertRaises(author_use_cases.DuplicateAuthorName):
            author_use_cases.update_author(self.uow, 2, self.draft)
        self.store.update_author.assert_not_called()

    def test_update_maps_database_duplicate_race(self):
        self.store.author_name_exists.return_value = False
        self.store.update_author.side_effect = DuplicateAuthorRecord()
        with self.assertRaises(author_use_cases.DuplicateAuthorName):
            author_use_cases.update_author(self.uow, 1, self.draft)

    def test_update_raises_not_found(self):
        self.store.author_name_exists.return_value = False
        self.store.update_author.return_value = None
        with self.assertRaisesRegex(author_use_cases.AuthorNotFound, "Author 8 was not found"):
            author_use_cases.update_author(self.uow, 8, self.draft)

    def test_grouped_books_delegates_to_persistence(self):
        groups = [AuthorBookGroup(self.author, ())]
        self.store.grouped_books.return_value = groups
        self.assertEqual(author_use_cases.get_books_grouped_by_author(self.uow), groups)


if __name__ == "__main__":
    unittest.main()
