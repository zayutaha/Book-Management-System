from mysql.connector import Error, IntegrityError

from home_library.domain import Book

from .errors import DuplicateISBNRecord, PersistenceError


BOOK_COLUMNS = (
    "b.id, b.title, b.isbn, b.price, b.author_id, a.name"
)
BOOK_FROM = " FROM books AS b JOIN authors AS a ON a.id = b.author_id"


def _book_from_row(row):
    return Book(
        id=row[0],
        title=row[1],
        isbn=row[2],
        price=row[3],
        author_id=row[4],
        author_name=row[5],
    )


def find_books(unit_of_work, search=""):
    cursor = unit_of_work._cursor()
    try:
        query = f"SELECT {BOOK_COLUMNS}{BOOK_FROM}"
        if search:
            pattern = f"%{search}%"
            query += " WHERE b.title LIKE %s OR b.isbn LIKE %s OR a.name LIKE %s"
            cursor.execute(query + " ORDER BY b.title", (pattern, pattern, pattern))
        else:
            cursor.execute(query + " ORDER BY b.title")
        return [_book_from_row(row) for row in cursor.fetchall()]
    except Error as error:
        raise PersistenceError(f"Could not read books: {error}") from error
    finally:
        cursor.close()


def find_book(unit_of_work, book_id):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            f"SELECT {BOOK_COLUMNS}{BOOK_FROM} WHERE b.id = %s",
            (book_id,),
        )
        row = cursor.fetchone()
        return _book_from_row(row) if row else None
    except Error as error:
        raise PersistenceError(f"Could not read book: {error}") from error
    finally:
        cursor.close()


def isbn_exists(unit_of_work, isbn, exclude_id=None):
    cursor = unit_of_work._cursor()
    try:
        if exclude_id is None:
            cursor.execute("SELECT id FROM books WHERE isbn = %s", (isbn,))
        else:
            cursor.execute(
                "SELECT id FROM books WHERE isbn = %s AND id <> %s",
                (isbn, exclude_id),
            )
        return cursor.fetchone() is not None
    except Error as error:
        raise PersistenceError(f"Could not check ISBN: {error}") from error
    finally:
        cursor.close()


def insert_book(unit_of_work, draft):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "INSERT INTO books (title, author_id, isbn, price) "
            "VALUES (%s, %s, %s, %s)",
            (draft.title, draft.author_id, draft.isbn, draft.price),
        )
        book_id = cursor.lastrowid
    except IntegrityError as error:
        if error.errno == 1062:
            raise DuplicateISBNRecord from error
        raise PersistenceError(f"Could not add book: {error}") from error
    except Error as error:
        raise PersistenceError(f"Could not add book: {error}") from error
    finally:
        cursor.close()
    return find_book(unit_of_work, book_id)


def update_book(unit_of_work, book_id, draft):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "UPDATE books SET title = %s, author_id = %s, isbn = %s, price = %s "
            "WHERE id = %s",
            (draft.title, draft.author_id, draft.isbn, draft.price, book_id),
        )
    except IntegrityError as error:
        if error.errno == 1062:
            raise DuplicateISBNRecord from error
        raise PersistenceError(f"Could not update book: {error}") from error
    except Error as error:
        raise PersistenceError(f"Could not update book: {error}") from error
    finally:
        cursor.close()
    return find_book(unit_of_work, book_id)


def delete_book(unit_of_work, book_id):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        return cursor.rowcount > 0
    except Error as error:
        raise PersistenceError(f"Could not delete book: {error}") from error
    finally:
        cursor.close()
