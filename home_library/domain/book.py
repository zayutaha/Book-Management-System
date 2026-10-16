import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .errors import InvalidISBN, InvalidPrice, InvalidTitle


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    isbn: str | None
    price: Decimal


@dataclass(frozen=True)
class BookDraft:
    title: str
    isbn: str | None
    price: Decimal

    def __post_init__(self):
        object.__setattr__(self, "title", validate_title(self.title))
        object.__setattr__(self, "isbn", normalize_isbn(self.isbn or ""))
        object.__setattr__(self, "price", parse_price(self.price))


def validate_title(value):
    if not isinstance(value, str):
        raise InvalidTitle("Title cannot be empty.")
    title = value.strip()
    if not title:
        raise InvalidTitle("Title cannot be empty.")
    if len(title) > 200:
        raise InvalidTitle("Title must be 200 characters or fewer.")
    return title


def normalize_isbn(value):
    if value is None or not str(value).strip():
        return None
    isbn = re.sub(r"[\s-]", "", str(value)).upper()
    if len(isbn) == 10 and re.fullmatch(r"\d{9}[\dX]", isbn):
        digits = [10 if char == "X" else int(char) for char in isbn]
        if sum((10 - index) * digit for index, digit in enumerate(digits)) % 11 == 0:
            return isbn
    if len(isbn) == 13 and isbn.isdigit():
        total = sum(
            int(digit) * (1 if index % 2 == 0 else 3)
            for index, digit in enumerate(isbn[:12])
        )
        if (10 - total % 10) % 10 == int(isbn[12]):
            return isbn
    raise InvalidISBN("Enter a valid ISBN-10 or ISBN-13, or leave it blank.")


def parse_price(value):
    text = str(value).strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", text):
        raise InvalidPrice("Enter a non-negative price with at most 2 decimal places.")
    try:
        price = Decimal(text)
    except InvalidOperation as error:
        raise InvalidPrice("Enter a valid price.") from error
    if price > Decimal("99999999.99"):
        raise InvalidPrice("Price must be less than ₹100,000,000.")
    return price.quantize(Decimal("0.01"))
