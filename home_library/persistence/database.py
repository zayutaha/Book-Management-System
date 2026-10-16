import os
from dataclasses import dataclass

import mysql.connector
from mysql.connector import Error

from .errors import PersistenceError
from .schema import initialize_schema
from .unit_of_work import UnitOfWork


@dataclass
class Database:
    _connection: object

    def unit_of_work(self):
        return UnitOfWork(self._connection)

    def close(self):
        self._connection.close()


def connect_database() -> Database:
    settings = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "schoolproject"),
    }
    connection = None
    try:
        connection = mysql.connector.connect(**settings)
        initialize_schema(connection)
        return Database(connection)
    except Error as error:
        if connection is not None:
            connection.close()
        raise PersistenceError(f"Could not connect to MySQL: {error}") from error
    except PersistenceError:
        if connection is not None:
            connection.close()
        raise
