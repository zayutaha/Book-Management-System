import re

from mysql.connector import Error

from .errors import PersistenceError

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


def use_database(cursor, database_name):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
    cursor.execute(f"USE `{database_name}`")


def initialize_schema(connection, database_name="home_library"):
    if not isinstance(database_name, str) or not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise PersistenceError("Database name contains unsupported characters.")

    cursor = None
    try:
        cursor = connection.cursor()
        use_database(cursor, database_name)
        _create_authors(cursor)
        _create_books(cursor)
        connection.commit()
    except Error as error:
        connection.rollback()
        raise PersistenceError(f"Could not initialize the database: {error}") from error
    finally:
        if cursor is not None:
            cursor.close()
