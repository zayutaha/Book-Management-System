import unittest
from unittest.mock import patch

from mysql.connector import Error

from home_library.persistence.errors import PersistenceError
from home_library.persistence.schema import initialize_schema
from home_library.persistence.unit_of_work import UnitOfWork


class FakeCursor:
    def __init__(self, failing_statement=None):
        self.statements = []
        self.closed = False
        self.failing_statement = failing_statement

    def execute(self, statement):
        self.statements.append(statement)
        if statement == self.failing_statement:
            raise Error("statement failed")

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.in_transaction = False
        self.cursor_value = FakeCursor()
        self.calls = []
        self.failure = None

    def cursor(self, **kwargs):
        self.calls.append(("cursor", kwargs))
        if self.failure == "cursor":
            raise Error("cursor failed")
        return self.cursor_value

    def start_transaction(self):
        self.calls.append(("start_transaction",))
        if self.failure == "start":
            raise Error("start failed")
        self.in_transaction = True

    def rollback(self):
        self.calls.append(("rollback",))
        if self.failure == "rollback":
            raise Error("rollback failed")
        self.in_transaction = False

    def commit(self):
        self.calls.append(("commit",))
        if self.failure == "commit":
            raise Error("commit failed")
        self.in_transaction = False


class UnitOfWorkTests(unittest.TestCase):
    def test_uncommitted_scope_rolls_back(self):
        connection = FakeConnection()
        with UnitOfWork(connection):
            pass
        self.assertIn(("rollback",), connection.calls)

    def test_committed_scope_does_not_roll_back(self):
        connection = FakeConnection()
        with UnitOfWork(connection) as uow:
            uow.commit()
        self.assertEqual(connection.calls.count(("rollback",)), 0)
        self.assertEqual(connection.calls.count(("commit",)), 1)

    def test_exception_scope_rolls_back_and_propagates(self):
        connection = FakeConnection()
        with self.assertRaisesRegex(RuntimeError, "failure"):
            with UnitOfWork(connection):
                raise RuntimeError("failure")
        self.assertEqual(connection.calls.count(("rollback",)), 1)

    def test_enter_clears_existing_transaction_before_starting(self):
        connection = FakeConnection()
        connection.in_transaction = True
        with UnitOfWork(connection):
            pass
        self.assertEqual(connection.calls[:2], [("rollback",), ("start_transaction",)])

    def test_cursor_requests_dictionary_option(self):
        connection = FakeConnection()
        uow = UnitOfWork(connection)
        self.assertIs(uow._cursor(dictionary=True), connection.cursor_value)
        self.assertEqual(connection.calls, [("cursor", {"dictionary": True})])

    def test_start_transaction_error_is_wrapped(self):
        connection = FakeConnection()
        connection.failure = "start"
        with self.assertRaisesRegex(PersistenceError, "Could not start transaction"):
            UnitOfWork(connection).__enter__()

    def test_cursor_error_is_wrapped(self):
        connection = FakeConnection()
        connection.failure = "cursor"
        with self.assertRaisesRegex(PersistenceError, "Could not open database cursor"):
            UnitOfWork(connection)._cursor()

    def test_commit_error_is_wrapped(self):
        connection = FakeConnection()
        connection.failure = "commit"
        with self.assertRaisesRegex(PersistenceError, "Could not commit transaction"):
            UnitOfWork(connection).commit()

    def test_rollback_error_without_prior_exception_is_wrapped(self):
        connection = FakeConnection()
        connection.failure = "rollback"
        with self.assertRaisesRegex(PersistenceError, "Could not roll back transaction"):
            with UnitOfWork(connection):
                pass

    def test_rollback_error_does_not_mask_original_exception(self):
        connection = FakeConnection()
        connection.failure = "rollback"
        with self.assertRaisesRegex(RuntimeError, "original"):
            with UnitOfWork(connection):
                raise RuntimeError("original")


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = FakeConnection()
        self.connection.cursor_value = FakeCursor()

    def test_creates_and_selects_requested_database_and_books_table(self):
        initialize_schema(self.connection, "home_library_test")
        statements = self.connection.cursor_value.statements
        self.assertEqual(statements[0], "CREATE DATABASE IF NOT EXISTS `home_library_test`")
        self.assertEqual(statements[1], "USE `home_library_test`")
        self.assertIn("isbn VARCHAR(13) NULL UNIQUE", statements[2])
        self.assertIn("price DECIMAL(10, 2) NOT NULL", statements[2])
        self.assertIn("CHECK (price >= 0)", statements[2])
        self.assertEqual(statements[3], "ALTER TABLE books MODIFY isbn VARCHAR(13) NULL")
        self.assertIn(("commit",), self.connection.calls)
        self.assertTrue(self.connection.cursor_value.closed)

    def test_rejects_unsafe_database_name_before_opening_cursor(self):
        with self.assertRaisesRegex(PersistenceError, "unsupported characters"):
            initialize_schema(self.connection, "unsafe-name; DROP DATABASE home_library")
        self.assertEqual(self.connection.calls, [])

    def test_mysql_schema_error_rolls_back_and_wraps(self):
        failing_statement = "USE `home_library_test`"
        self.connection.cursor_value = FakeCursor(failing_statement)
        with self.assertRaisesRegex(PersistenceError, "Could not initialize the database"):
            initialize_schema(self.connection, "home_library_test")
        self.assertIn(("rollback",), self.connection.calls)
        self.assertTrue(self.connection.cursor_value.closed)


if __name__ == "__main__":
    unittest.main()
