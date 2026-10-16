import unittest
from unittest.mock import Mock, patch

from mysql.connector import Error

from home_library.persistence.database import connect_database
from home_library.persistence.errors import PersistenceError


class DatabaseConnectionTests(unittest.TestCase):
    @patch("home_library.persistence.database.initialize_schema")
    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_uses_default_connection_settings_and_database(self, connect, initialize):
        connection = Mock()
        connect.return_value = connection
        with patch.dict("os.environ", {}, clear=True):
            database = connect_database()
        self.assertIs(database._connection, connection)
        connect.assert_called_once_with(
            host="localhost",
            port=3306,
            user="root",
            password="schoolproject",
        )
        initialize.assert_called_once_with(connection, "home_library")

    @patch("home_library.persistence.database.initialize_schema")
    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_reads_connection_and_database_settings_from_environment(self, connect, initialize):
        connection = Mock()
        connect.return_value = connection
        settings = {
            "MYSQL_HOST": "db.example",
            "MYSQL_PORT": "3307",
            "MYSQL_USER": "reader",
            "MYSQL_PASSWORD": "secret",
            "MYSQL_DATABASE_NAME": "family_shelf",
        }
        with patch.dict("os.environ", settings, clear=True):
            connect_database()
        connect.assert_called_once_with(
            host="db.example",
            port=3307,
            user="reader",
            password="secret",
        )
        initialize.assert_called_once_with(connection, "family_shelf")

    @patch("home_library.persistence.database.initialize_schema")
    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_explicit_database_name_overrides_environment(self, connect, initialize):
        connection = Mock()
        connect.return_value = connection
        with patch.dict("os.environ", {"MYSQL_DATABASE_NAME": "configured"}):
            connect_database("explicit")
        initialize.assert_called_once_with(connection, "explicit")

    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_connection_error_is_wrapped(self, connect):
        connect.side_effect = Error("offline")
        with self.assertRaisesRegex(PersistenceError, "Could not connect to MySQL"):
            connect_database()

    @patch("home_library.persistence.database.initialize_schema")
    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_schema_connection_error_closes_connection_and_is_wrapped(self, connect, initialize):
        connection = Mock()
        connect.return_value = connection
        initialize.side_effect = Error("schema failure")
        with self.assertRaisesRegex(PersistenceError, "Could not connect to MySQL"):
            connect_database("test_db")
        connection.close.assert_called_once_with()

    @patch("home_library.persistence.database.initialize_schema")
    @patch("home_library.persistence.database.mysql.connector.connect")
    def test_schema_persistence_error_closes_and_preserves_error(self, connect, initialize):
        connection = Mock()
        connect.return_value = connection
        expected = PersistenceError("invalid schema")
        initialize.side_effect = expected
        with self.assertRaises(PersistenceError) as raised:
            connect_database("test_db")
        self.assertIs(raised.exception, expected)
        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
