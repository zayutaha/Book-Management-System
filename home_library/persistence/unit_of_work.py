from mysql.connector import Error

from .errors import PersistenceError


class UnitOfWork:
    def __init__(self, connection):
        self._connection = connection
        self._committed = False

    def __enter__(self):
        try:
            if self._connection.in_transaction:
                self._connection.rollback()
            self._connection.start_transaction()
            self._committed = False
            return self
        except Error as error:
            raise PersistenceError(f"Could not start transaction: {error}") from error

    def __exit__(self, exception_type, exception, traceback):
        if exception_type is not None or not self._committed:
            try:
                self._connection.rollback()
            except Error as error:
                if exception_type is None:
                    raise PersistenceError(f"Could not roll back transaction: {error}") from error
        return False

    def commit(self):
        try:
            self._connection.commit()
            self._committed = True
        except Error as error:
            raise PersistenceError(f"Could not commit transaction: {error}") from error

    def _cursor(self, dictionary=False):
        try:
            return self._connection.cursor(dictionary=dictionary)
        except Error as error:
            raise PersistenceError(f"Could not open database cursor: {error}") from error
