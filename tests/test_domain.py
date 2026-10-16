import unittest
from decimal import Decimal

from home_library.domain import (
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

    def test_isbn_is_optional(self):
        self.assertIsNone(normalize_isbn(""))
        self.assertIsNone(normalize_isbn(None))

    def test_rejects_invalid_isbn_checksum(self):
        with self.assertRaises(InvalidISBN):
            normalize_isbn("9780306406158")

    def test_validates_and_normalizes_title(self):
        self.assertEqual(validate_title("  Dune  "), "Dune")
        with self.assertRaises(InvalidTitle):
            validate_title("   ")
        with self.assertRaises(InvalidTitle):
            validate_title("x" * 201)

    def test_price_uses_two_decimal_places(self):
        self.assertEqual(parse_price("19.5"), Decimal("19.50"))
        with self.assertRaises(InvalidPrice):
            parse_price("-1")
        with self.assertRaises(InvalidPrice):
            parse_price("1.234")

    def test_book_draft_applies_domain_rules(self):
        draft = BookDraft(" Dune ", "978-0-306-40615-7", Decimal("12.5"))
        self.assertEqual(draft.title, "Dune")
        self.assertEqual(draft.isbn, "9780306406157")
        self.assertEqual(draft.price, Decimal("12.50"))


if __name__ == "__main__":
    unittest.main()
