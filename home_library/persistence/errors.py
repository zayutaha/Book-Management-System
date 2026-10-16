class PersistenceError(Exception):
    pass


class DuplicateISBNRecord(PersistenceError):
    pass
