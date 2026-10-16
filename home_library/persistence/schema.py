import re
import warnings

from mysql.connector import Error

from .errors import PersistenceError


SCHEMA_VERSION = 2


def _count(cursor, query, params=()):
    cursor.execute(query, params)
    return cursor.fetchone()[0]


def _create_authors(cursor):
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS authors ("
        "id INT AUTO_INCREMENT PRIMARY KEY, "
        "name VARCHAR(200) CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_0900_as_ci NOT NULL UNIQUE, "
        "birth_date DATE NOT NULL)"
    )


def _create_books(cursor):
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS books ("
        "id INT AUTO_INCREMENT PRIMARY KEY, "
        "title VARCHAR(200) NOT NULL, "
        "author_id INT NOT NULL, "
        "isbn VARCHAR(13) NULL UNIQUE, "
        "price DECIMAL(10, 2) NOT NULL, "
        "CHECK (price >= 0), "
        "CONSTRAINT fk_books_author FOREIGN KEY (author_id) "
        "REFERENCES authors(id) ON DELETE RESTRICT)"
    )


def _table_exists(cursor, table_name):
    return bool(
        _count(
            cursor,
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s",
            (table_name,),
        )
    )


def _column_exists(cursor, table_name, column_name):
    return bool(
        _count(
            cursor,
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
            (table_name, column_name),
        )
    )


def _foreign_key_exists(cursor):
    return bool(
        _count(
            cursor,
            "SELECT COUNT(*) FROM information_schema.key_column_usage "
            "WHERE table_schema = DATABASE() AND table_name = 'books' "
            "AND column_name = 'author_id' AND referenced_table_name = 'authors'",
        )
    )


def initialize_schema(connection, database_name="home_library"):
    if not isinstance(database_name, str) or not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise PersistenceError("Database name contains unsupported characters.")
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        cursor.execute(f"USE `{database_name}`")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INT NOT NULL PRIMARY KEY)"
        )
        versioned = _count(
            cursor,
            "SELECT COUNT(*) FROM schema_version WHERE version = %s",
            (SCHEMA_VERSION,),
        )
        if versioned:
            cursor.execute("ALTER TABLE books MODIFY isbn VARCHAR(13) NULL")
            connection.commit()
            return

        books_exist = _table_exists(cursor, "books")
        _create_authors(cursor)
        if not books_exist:
            _create_books(cursor)
        elif not _column_exists(cursor, "books", "author_id"):
            warnings.warn(
                "The Home Library migration will clear old prototype books "
                "because those records have no author.",
                RuntimeWarning,
                stacklevel=2,
            )
            cursor.execute("DELETE FROM books")
            cursor.execute(
                "ALTER TABLE books ADD COLUMN author_id INT NOT NULL AFTER title"
            )
            cursor.execute(
                "ALTER TABLE books ADD CONSTRAINT fk_books_author "
                "FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT"
            )
        else:
            cursor.execute("ALTER TABLE books MODIFY author_id INT NOT NULL")
            if not _foreign_key_exists(cursor):
                cursor.execute(
                    "ALTER TABLE books ADD CONSTRAINT fk_books_author "
                    "FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT"
                )
        cursor.execute("ALTER TABLE books MODIFY isbn VARCHAR(13) NULL")
        cursor.execute(
            "INSERT IGNORE INTO schema_version (version) VALUES (%s)",
            (SCHEMA_VERSION,),
        )
        connection.commit()
    except Error as error:
        connection.rollback()
        raise PersistenceError(f"Could not initialize the database: {error}") from error
    finally:
        if cursor is not None:
            cursor.close()
