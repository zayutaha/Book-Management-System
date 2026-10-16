import re

from mysql.connector import Error

from .errors import PersistenceError


def initialize_schema(connection, database_name="home_library"):
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise PersistenceError("Database name contains unsupported characters.")
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        cursor.execute(f"USE `{database_name}`")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS books ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "title VARCHAR(200) NOT NULL, "
            "isbn VARCHAR(13) NULL UNIQUE, "
            "price DECIMAL(10, 2) NOT NULL, "
            "CHECK (price >= 0))"
        )
        cursor.execute("ALTER TABLE books MODIFY isbn VARCHAR(13) NULL")
        connection.commit()
    except Error as error:
        connection.rollback()
        raise PersistenceError(f"Could not initialize the database: {error}") from error
    finally:
        cursor.close()
