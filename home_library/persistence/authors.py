from mysql.connector import Error, IntegrityError

from home_library.domain import Author, AuthorBookGroup, Book

from .errors import DuplicateAuthorRecord, PersistenceError


def _author_from_row(row):
    return Author(id=row[0], name=row[1], birth_date=row[2], book_count=row[3])


def find_authors(unit_of_work, search=""):
    cursor = unit_of_work._cursor()
    try:
        if search:
            cursor.execute(
                "SELECT a.id, a.name, a.birth_date, COUNT(b.id) "
                "FROM authors AS a LEFT JOIN books AS b ON b.author_id = a.id "
                "WHERE a.name LIKE %s "
                "GROUP BY a.id, a.name, a.birth_date ORDER BY a.name",
                (f"%{search}%",),
            )
        else:
            cursor.execute(
                "SELECT a.id, a.name, a.birth_date, COUNT(b.id) "
                "FROM authors AS a LEFT JOIN books AS b ON b.author_id = a.id "
                "GROUP BY a.id, a.name, a.birth_date ORDER BY a.name"
            )
        return [_author_from_row(row) for row in cursor.fetchall()]
    except Error as error:
        raise PersistenceError(f"Could not read authors: {error}") from error
    finally:
        cursor.close()


def find_author(unit_of_work, author_id):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "SELECT a.id, a.name, a.birth_date, COUNT(b.id) "
            "FROM authors AS a LEFT JOIN books AS b ON b.author_id = a.id "
            "WHERE a.id = %s GROUP BY a.id, a.name, a.birth_date",
            (author_id,),
        )
        row = cursor.fetchone()
        return _author_from_row(row) if row else None
    except Error as error:
        raise PersistenceError(f"Could not read author: {error}") from error
    finally:
        cursor.close()


def author_name_exists(unit_of_work, name, exclude_id=None):
    cursor = unit_of_work._cursor()
    try:
        if exclude_id is None:
            cursor.execute("SELECT id FROM authors WHERE name = %s", (name,))
        else:
            cursor.execute(
                "SELECT id FROM authors WHERE name = %s AND id <> %s",
                (name, exclude_id),
            )
        return cursor.fetchone() is not None
    except Error as error:
        raise PersistenceError(f"Could not check author name: {error}") from error
    finally:
        cursor.close()


def author_id_exists(unit_of_work, author_id):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute("SELECT id FROM authors WHERE id = %s", (author_id,))
        return cursor.fetchone() is not None
    except Error as error:
        raise PersistenceError(f"Could not check author: {error}") from error
    finally:
        cursor.close()


def insert_author(unit_of_work, draft):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "INSERT INTO authors (name, birth_date) VALUES (%s, %s)",
            (draft.name, draft.birth_date),
        )
        author_id = cursor.lastrowid
    except IntegrityError as error:
        if error.errno == 1062:
            raise DuplicateAuthorRecord from error
        raise PersistenceError(f"Could not add author: {error}") from error
    except Error as error:
        raise PersistenceError(f"Could not add author: {error}") from error
    finally:
        cursor.close()
    return find_author(unit_of_work, author_id)


def update_author(unit_of_work, author_id, draft):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "UPDATE authors SET name = %s, birth_date = %s WHERE id = %s",
            (draft.name, draft.birth_date, author_id),
        )
    except IntegrityError as error:
        if error.errno == 1062:
            raise DuplicateAuthorRecord from error
        raise PersistenceError(f"Could not update author: {error}") from error
    except Error as error:
        raise PersistenceError(f"Could not update author: {error}") from error
    finally:
        cursor.close()
    return find_author(unit_of_work, author_id)


def grouped_books(unit_of_work):
    cursor = unit_of_work._cursor()
    try:
        cursor.execute(
            "SELECT a.id, a.name, a.birth_date, b.id, b.title, b.isbn, b.price "
            "FROM authors AS a LEFT JOIN books AS b ON b.author_id = a.id "
            "ORDER BY a.name, b.title"
        )
        groups = {}
        for row in cursor.fetchall():
            author_id, name, birth_date, book_id, title, isbn, price = row
            if author_id not in groups:
                groups[author_id] = {"name": name, "birth_date": birth_date, "books": []}
            if book_id is not None:
                groups[author_id]["books"].append(
                    Book(
                        id=book_id,
                        title=title,
                        isbn=isbn,
                        price=price,
                        author_id=author_id,
                        author_name=name,
                    )
                )
        return [
            AuthorBookGroup(
                author=Author(
                    id=author_id,
                    name=values["name"],
                    birth_date=values["birth_date"],
                    book_count=len(values["books"]),
                ),
                books=tuple(values["books"]),
            )
            for author_id, values in groups.items()
        ]
    except Error as error:
        raise PersistenceError(f"Could not group books by author: {error}") from error
    finally:
        cursor.close()
