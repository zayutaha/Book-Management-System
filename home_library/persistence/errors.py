class PersistenceError(Exception):
    pass


class DuplicateISBNRecord(PersistenceError):
    pass


class DuplicateAuthorRecord(PersistenceError):
    pass
