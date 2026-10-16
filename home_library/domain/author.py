import unicodedata
from dataclasses import dataclass
from datetime import date, datetime

from .errors import InvalidAuthorName, InvalidBirthDate


@dataclass(frozen=True)
class Author:
    id: int
    name: str
    birth_date: date
    book_count: int


@dataclass(frozen=True)
class AuthorBookGroup:
    author: Author
    books: tuple


@dataclass(frozen=True)
class AuthorDraft:
    name: str
    birth_date: date

    def __post_init__(self):
        object.__setattr__(self, "name", validate_author_name(self.name))
        object.__setattr__(self, "birth_date", parse_birth_date(self.birth_date))


def validate_author_name(value):
    if not isinstance(value, str):
        raise InvalidAuthorName("Author name must contain at least two characters.")
    name = value.strip()
    if len(name) < 2:
        raise InvalidAuthorName("Author name must contain at least two characters.")
    if len(name) > 200:
        raise InvalidAuthorName("Author name must be 200 characters or fewer.")
    if not any(character.isalpha() for character in name):
        raise InvalidAuthorName("Author name must include a letter.")
    if any(unicodedata.category(character).startswith("N") for character in name):
        raise InvalidAuthorName("Author name cannot contain numbers.")
    return name


def parse_birth_date(value):
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        birth_date = value
    elif isinstance(value, str):
        try:
            birth_date = date.fromisoformat(value.strip())
        except ValueError as error:
            raise InvalidBirthDate("Enter a valid date in YYYY-MM-DD format.") from error
    else:
        raise InvalidBirthDate("Enter a valid date in YYYY-MM-DD format.")
    if birth_date > date.today():
        raise InvalidBirthDate("Birth date cannot be in the future.")
    return birth_date
