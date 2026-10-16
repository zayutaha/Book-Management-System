import unittest
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from decimal import Decimal

from home_library.domain import (
    Author,
    AuthorDraft,
    Book,
    BookDraft,
    InvalidAuthorName,
    InvalidBirthDate,
    InvalidISBN,
    InvalidPrice,
    InvalidTitle,
    normalize_isbn,
    parse_price,
    parse_birth_date,
    validate_author_name,
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
        draft = BookDraft(" Dune ", "978-0-306-40615-7", Decimal("12.5"), 1)
        self.assertEqual(draft.title, "Dune")
        self.assertEqual(draft.isbn, "9780306406157")
        self.assertEqual(draft.price, Decimal("12.50"))

    def test_draft_accepts_optional_isbn(self):
        self.assertIsNone(BookDraft("Dune", None, "0", 1).isbn)

    def test_book_and_draft_are_immutable(self):
        book = Book(1, "Dune", None, Decimal("12.00"), 1, "Frank Herbert")
        draft = BookDraft("Dune", None, "12", 1)
        with self.assertRaises(FrozenInstanceError):
            book.title = "Changed"
        with self.assertRaises(FrozenInstanceError):
            draft.title = "Changed"

    def test_book_draft_rejects_missing_or_invalid_author_id(self):
        for author_id in (None, 0, -1, "1", True):
            with self.subTest(author_id=author_id):
                with self.assertRaises(ValueError):
                    BookDraft("Dune", None, "12", author_id)


class AuthorDomainTests(unittest.TestCase):
    def test_author_name_is_trimmed_and_accepts_unicode_and_punctuation(self):
        self.assertEqual(validate_author_name("  J. R. R. Tolkien  "), "J. R. R. Tolkien")
        self.assertEqual(validate_author_name("  Émile Zola  "), "Émile Zola")

    def test_author_name_rejects_blank_short_digit_only_and_numeric_values(self):
        for value in ("", "  ", "A", "123", "James 2", None, 8, "١abc"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidAuthorName):
                    validate_author_name(value)

    def test_author_name_accepts_200_characters_and_rejects_longer_names(self):
        self.assertEqual(len(validate_author_name("A" * 200)), 200)
        with self.assertRaises(InvalidAuthorName):
            validate_author_name("A" * 201)

    def test_birth_date_parses_iso_date_and_date_objects(self):
        expected = date(1970, 5, 21)
        self.assertEqual(parse_birth_date("1970-05-21"), expected)
        self.assertEqual(parse_birth_date(expected), expected)

    def test_birth_date_rejects_invalid_and_future_dates(self):
        for value in ("2023-02-29", "21-05-1970", "not-a-date", None, 1970):
            with self.subTest(value=value):
                with self.assertRaises(InvalidBirthDate):
                    parse_birth_date(value)
        with self.assertRaises(InvalidBirthDate):
            parse_birth_date(date.today() + timedelta(days=1))

    def test_author_draft_normalizes_both_required_fields(self):
        draft = AuthorDraft("  Ursula Le Guin ", "1929-10-21")
        self.assertEqual(draft.name, "Ursula Le Guin")
        self.assertEqual(draft.birth_date, date(1929, 10, 21))

    def test_author_record_includes_computed_book_count(self):
        author = Author(4, "Ursula Le Guin", date(1929, 10, 21), 3)
        self.assertEqual(author.book_count, 3)


if __name__ == "__main__":
    unittest.main()
