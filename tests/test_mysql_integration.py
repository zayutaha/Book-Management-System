import os
import re
import unittest
from decimal import Decimal
from uuid import uuid4

import mysql.connector

from home_library.domain import BookDraft
from home_library.persistence.database import connect_database
from home_library.persistence.errors import PersistenceError
from home_library.use_cases.books import (
    BookNotFound,
    DuplicateISBN,
    create_book,
    delete_book,
    get_books,
    update_book,
)


ENABLED = os.getenv("RUN_MYSQL_INTEGRATION") == "1"


@unittest.skipUnless(ENABLED, "set RUN_MYSQL_INTEGRATION=1 to run disposable MySQL tests")
class MySQLBookIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database_name = f"home_library_test_{uuid4().hex}"
        cls.settings = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "schoolproject"),
        }
        if not re.fullmatch(r"home_library_test_[a-f0-9]+", cls.database_name):
            raise AssertionError("Generated test database name was unsafe")

        admin = mysql.connector.connect(**cls.settings)
        cursor = admin.cursor()
        try:
            cursor.execute(f"CREATE DATABASE `{cls.database_name}`")
            cursor.execute(f"USE `{cls.database_name}`")
            cursor.execute(
                "CREATE TABLE books ("
                "id INT AUTO_INCREMENT PRIMARY KEY, "
                "title VARCHAR(200) NOT NULL, "
                "isbn VARCHAR(13) NOT NULL UNIQUE, "
                "price DECIMAL(10, 2) NOT NULL)"
            )
            cursor.execute(
                "INSERT INTO books (title, isbn, price) VALUES (%s, %s, %s)",
                ("Migration check", "9780306406157", Decimal("1.25")),
            )
            admin.commit()
        except Exception:
            admin.rollback()
            raise
        finally:
            cursor.close()
            admin.close()

        cls.database = connect_database(cls.database_name)
        cursor = cls.database._connection.cursor()
        try:
            cursor.execute(
                "SELECT IS_NULLABLE FROM information_schema.columns "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'books' AND COLUMN_NAME = 'isbn'",
                (cls.database_name,),
            )
            cls.migrated_isbn_nullable = cursor.fetchone()[0]
            cursor.execute("SELECT title, isbn, price FROM books WHERE title = %s", ("Migration check",))
            cls.migrated_existing_record = cursor.fetchone()
        finally:
            cursor.close()

    @classmethod
    def tearDownClass(cls):
        database = getattr(cls, "database", None)
        if database is not None:
            database.close()
        database_name = getattr(cls, "database_name", None)
        if database_name and re.fullmatch(r"home_library_test_[a-f0-9]+", database_name):
            admin = mysql.connector.connect(**cls.settings)
            cursor = admin.cursor()
            try:
                cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
            finally:
                cursor.close()
                admin.close()

    def setUp(self):
        with self.database.unit_of_work() as uow:
            for book in get_books(uow):
                delete_book(uow, book.id)
            uow.commit()

    def add_book(self, title, isbn=None, price="0"):
        draft = BookDraft(title, isbn, price)
        with self.database.unit_of_work() as uow:
            book = create_book(uow, draft)
            uow.commit()
            return book

    def test_schema_migration_makes_isbn_optional_and_preserves_existing_records(self):
        self.assertEqual(self.migrated_isbn_nullable, "YES")
        self.assertEqual(self.migrated_existing_record[0:2], ("Migration check", "9780306406157"))
        self.assertEqual(self.migrated_existing_record[2], Decimal("1.25"))

    def test_create_and_read_book_with_optional_isbn_and_decimal_price(self):
        created = self.add_book("The Hobbit", None, "19.5")
        self.assertIsNotNone(created.id)
        self.assertEqual(created.title, "The Hobbit")
        self.assertIsNone(created.isbn)
        self.assertEqual(created.price, Decimal("19.50"))
        with self.database.unit_of_work() as uow:
            found = get_books(uow)
            self.assertEqual(found, [created])

    def test_multiple_books_can_have_blank_isbn(self):
        self.add_book("Book One")
        self.add_book("Book Two")
        with self.database.unit_of_work() as uow:
            self.assertEqual(len(get_books(uow)), 2)

    def test_search_matches_title_and_isbn(self):
        title_match = self.add_book("A Tale of Two Cities", "9780306406157")
        isbn_match = self.add_book("Another Story", "080442957X")
        with self.database.unit_of_work() as uow:
            self.assertEqual(get_books(uow, "Two Cities"), [title_match])
            self.assertEqual(get_books(uow, "080442"), [isbn_match])

    def test_search_is_parameterized_for_quotes_in_title(self):
        book = self.add_book("Reader's Guide")
        with self.database.unit_of_work() as uow:
            self.assertEqual(get_books(uow, "Reader's"), [book])

    def test_books_are_returned_in_title_order(self):
        zulu = self.add_book("Zulu")
        alpha = self.add_book("Alpha")
        with self.database.unit_of_work() as uow:
            self.assertEqual(get_books(uow), [alpha, zulu])

    def test_duplicate_isbn_is_rejected(self):
        self.add_book("First", "9780306406157")
        with self.database.unit_of_work() as uow:
            with self.assertRaises(DuplicateISBN):
                create_book(uow, BookDraft("Second", "9780306406157", "2"))

    def test_update_can_keep_its_own_isbn(self):
        book = self.add_book("Original", "9780306406157", "10")
        revised = BookDraft("Revised", "9780306406157", "15.25")
        with self.database.unit_of_work() as uow:
            result = update_book(uow, book.id, revised)
            uow.commit()
        self.assertEqual((result.title, result.isbn, result.price), ("Revised", "9780306406157", Decimal("15.25")))

    def test_update_can_remove_isbn(self):
        book = self.add_book("Original", "9780306406157")
        with self.database.unit_of_work() as uow:
            result = update_book(uow, book.id, BookDraft("Revised", None, "0"))
            uow.commit()
        self.assertIsNone(result.isbn)

    def test_update_rejects_isbn_used_by_another_book(self):
        first = self.add_book("First", "9780306406157")
        second = self.add_book("Second", "080442957X")
        with self.database.unit_of_work() as uow:
            with self.assertRaises(DuplicateISBN):
                update_book(uow, second.id, BookDraft("Second", first.isbn, "0"))

    def test_update_of_missing_book_raises_not_found(self):
        with self.database.unit_of_work() as uow:
            with self.assertRaises(BookNotFound):
                update_book(uow, 999999, BookDraft("Missing", None, "0"))

    def test_delete_removes_book_after_commit(self):
        book = self.add_book("Temporary")
        with self.database.unit_of_work() as uow:
            delete_book(uow, book.id)
            uow.commit()
        with self.database.unit_of_work() as uow:
            self.assertEqual(get_books(uow), [])

    def test_delete_of_missing_book_raises_not_found(self):
        with self.database.unit_of_work() as uow:
            with self.assertRaises(BookNotFound):
                delete_book(uow, 999999)

    def test_uncommitted_create_is_rolled_back(self):
        with self.database.unit_of_work() as uow:
            created = create_book(uow, BookDraft("Rolled Back", None, "1"))
        with self.database.unit_of_work() as uow:
            self.assertIsNone(next((book for book in get_books(uow) if book.id == created.id), None))

    def test_schema_rejects_unsafe_database_name(self):
        with self.assertRaises(PersistenceError):
            connect_database("invalid-name")


if __name__ == "__main__":
    unittest.main()
