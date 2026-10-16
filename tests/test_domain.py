import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from home_library.domain import (
    Book,
    BookDraft,
    InvalidISBN,
    InvalidPrice,
    InvalidTitle,
    normalize_isbn,
    parse_price,
    validate_title,
)


class BookDomainTests(unittest.TestCase):
    def test_normalizes_valid_isbn_10_and_13(self):
        self.assertEqual(normalize_isbn("0-306-40615-2"), "0306406152")
        self.assertEqual(normalize_isbn("978-0-306-40615-7"), "9780306406157")

    def test_normalizes_lowercase_isbn_10_check_digit_x(self):
        self.assertEqual(normalize_isbn("0-8044-2957-x"), "080442957X")

    def test_isbn_is_optional_for_blank_values(self):
        for value in (None, "", "   "):
            with self.subTest(value=value):
                self.assertIsNone(normalize_isbn(value))

    def test_rejects_invalid_isbn_checksums(self):
        for value in ("9780306406158", "0306406153", "0804429570"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidISBN):
                    normalize_isbn(value)

    def test_rejects_isbn_with_invalid_length_or_characters(self):
        for value in ("123", "12345678901", "978030640615A", "ABCDEFGHIJ"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidISBN):
                    normalize_isbn(value)

    def test_title_is_trimmed(self):
        self.assertEqual(validate_title("  Dune  "), "Dune")

    def test_title_accepts_exact_maximum_length(self):
        title = "x" * 200
        self.assertEqual(validate_title(title), title)

    def test_title_rejects_empty_whitespace_non_text_and_too_long_values(self):
        for value in ("", "   ", None, 7, "x" * 201):
            with self.subTest(value=value):
                with self.assertRaises(InvalidTitle):
                    validate_title(value)

    def test_price_normalizes_to_two_decimal_places(self):
        cases = (("19.5", "19.50"), ("0", "0.00"), ("0004.20", "4.20"), (12, "12.00"))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(parse_price(value), Decimal(expected))

    def test_price_accepts_maximum_database_value(self):
        self.assertEqual(parse_price("99999999.99"), Decimal("99999999.99"))

    def test_price_rejects_negative_malformed_and_out_of_range_values(self):
        for value in ("-1", "1.234", "1,000", "₹10", "", "abc", "1e2", "100000000"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidPrice):
                    parse_price(value)

    def test_draft_normalizes_every_field(self):
        draft = BookDraft(" Dune ", "978-0-306-40615-7", Decimal("12.5"))
        self.assertEqual(draft.title, "Dune")
        self.assertEqual(draft.isbn, "9780306406157")
        self.assertEqual(draft.price, Decimal("12.50"))

    def test_draft_accepts_optional_isbn(self):
        self.assertIsNone(BookDraft("Dune", None, "0").isbn)

    def test_book_and_draft_are_immutable(self):
        book = Book(1, "Dune", None, Decimal("12.00"))
        draft = BookDraft("Dune", None, "12")
        with self.assertRaises(FrozenInstanceError):
            book.title = "Changed"
        with self.assertRaises(FrozenInstanceError):
            draft.title = "Changed"


if __name__ == "__main__":
    unittest.main()
