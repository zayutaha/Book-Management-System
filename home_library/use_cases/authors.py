from home_library.domain import Author, AuthorDraft, AuthorBookGroup
from home_library.persistence import authors as author_store
from home_library.persistence.errors import DuplicateAuthorRecord


class AuthorNotFound(Exception):
    pass


class DuplicateAuthorName(Exception):
    pass


def get_authors(unit_of_work, search="") -> list[Author]:
    return author_store.find_authors(unit_of_work, search.strip())


def find_author(unit_of_work, author_id: int) -> Author | None:
    return author_store.find_author(unit_of_work, author_id)


def author_name_conflict(unit_of_work, name: str, exclude_id=None) -> bool:
    return author_store.author_name_exists(unit_of_work, name, exclude_id)


def create_author(unit_of_work, draft: AuthorDraft) -> Author:
    if author_name_conflict(unit_of_work, draft.name):
        raise DuplicateAuthorName("An author with that name already exists.")
    try:
        return author_store.insert_author(unit_of_work, draft)
    except DuplicateAuthorRecord as error:
        raise DuplicateAuthorName("An author with that name already exists.") from error


def update_author(unit_of_work, author_id: int, draft: AuthorDraft) -> Author:
    if author_name_conflict(unit_of_work, draft.name, author_id):
        raise DuplicateAuthorName("An author with that name already exists.")
    try:
        author = author_store.update_author(unit_of_work, author_id, draft)
    except DuplicateAuthorRecord as error:
        raise DuplicateAuthorName("An author with that name already exists.") from error
    if author is None:
        raise AuthorNotFound(f"Author {author_id} was not found.")
    return author


def get_books_grouped_by_author(unit_of_work) -> list[AuthorBookGroup]:
    return author_store.grouped_books(unit_of_work)
