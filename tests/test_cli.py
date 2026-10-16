import unittest
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console

import main as cli
from home_library.domain import Book, BookDraft
from home_library.persistence import PersistenceError
from home_library.use_cases.books import BookNotFound, DuplicateISBN


def make_book(book_id=1, title="Dune", isbn="9780306406157", price="12.50"):
    return Book(book_id, title, isbn, Decimal(price))


class PromptTests(unittest.TestCase):
    @patch("main.ask")
    @patch("main.questionary.select")
    def test_choose_builds_select_prompt_and_returns_answer(self, select, ask):
        select.return_value = "Add book"
        ask.return_value = "Add book"
        choices = ["Add book", "Back"]
        self.assertEqual(cli.choose("Choose", choices), "Add book")
        select.assert_called_once()
        args, kwargs = select.call_args
        self.assertEqual(args[0], "Choose")
        self.assertEqual(kwargs["choices"], choices)
        self.assertEqual(kwargs["instruction"], "(↑/↓ move, Enter select, Esc back)")
        self.assertIs(ask.call_args.args[0], select.return_value)

    @patch("main.ask")
    @patch("main.questionary.text")
    def test_text_input_passes_default_to_prompt(self, text, ask):
        text.return_value = object()
        ask.return_value = "Dune"
        self.assertEqual(cli.text_input("Book title", "Old title"), "Dune")
        text.assert_called_once_with("Book title", default="Old title", style=cli.question_style)

    def test_escape_key_binding_returns_none_from_prompt(self):
        application = SimpleNamespace(key_bindings=KeyBindings())
        prompt = MagicMock()
        prompt.application = application
        prompt.ask.return_value = "chosen"
        self.assertEqual(cli.ask(prompt), "chosen")
        bindings = application.key_bindings.get_bindings_for_keys((Keys.Escape,))
        self.assertTrue(bindings)
        event = MagicMock()
        bindings[-1].handler(event)
        event.app.exit.assert_called_once_with(result=None)
        prompt.ask.assert_called_once_with(kbi_msg="")


class InputFlowTests(unittest.TestCase):
    def setUp(self):
        self.database = MagicMock()

    @patch("main.console.print")
    @patch("main.text_input", side_effect=["", "  Dune  "])
    def test_ask_title_retries_empty_input_and_trims_valid_input(self, text_input, print_message):
        self.assertEqual(cli.ask_title(), "Dune")
        self.assertEqual(text_input.call_args_list, [call("Book title", ""), call("Book title", "")])
        print_message.assert_called_once()

    @patch("main.console.print")
    @patch("main.text_input", side_effect=["bad-isbn", "978-0-306-40615-7"])
    @patch("main.isbn_conflict", return_value=False)
    def test_ask_isbn_retries_invalid_isbn(self, conflict, text_input, print_message):
        self.assertEqual(cli.ask_isbn(self.database), "9780306406157")
        self.assertEqual(text_input.call_args_list, [
            call("ISBN-10 or ISBN-13 (optional)", ""),
            call("ISBN-10 or ISBN-13 (optional)", "bad-isbn"),
        ])
        conflict.assert_called_once_with(self.database, "9780306406157", None)
        print_message.assert_called_once()

    @patch("main.console.print")
    @patch("main.text_input", side_effect=["9780306406157", "978-0-306-40615-7"])
    @patch("main.isbn_conflict", side_effect=[True, False])
    def test_ask_isbn_retries_duplicate_isbn(self, conflict, text_input, print_message):
        self.assertEqual(cli.ask_isbn(self.database), "9780306406157")
        self.assertEqual(conflict.call_count, 2)
        print_message.assert_called_once()

    @patch("main.text_input", return_value="   ")
    def test_ask_isbn_accepts_blank_as_optional(self, text_input):
        self.assertIsNone(cli.ask_isbn(self.database))

    @patch("main.text_input", return_value=None)
    def test_ask_isbn_returns_cancellation_sentinel_on_escape(self, text_input):
        self.assertIs(cli.ask_isbn(self.database), cli.CANCELLED)

    @patch("main.console.print")
    @patch("main.text_input", side_effect=["-1", "10.25"])
    def test_ask_price_retries_invalid_amount(self, text_input, print_message):
        self.assertEqual(cli.ask_price(), Decimal("10.25"))
        self.assertEqual(text_input.call_args_list, [
            call("Price in INR", ""),
            call("Price in INR", "-1"),
        ])
        print_message.assert_called_once()

    @patch("main.text_input", return_value=None)
    def test_ask_price_returns_none_when_cancelled(self, text_input):
        self.assertIsNone(cli.ask_price())

    @patch("main.ask_price", return_value=Decimal("8.00"))
    @patch("main.ask_isbn", return_value=None)
    @patch("main.ask_title", return_value="New title")
    def test_book_fields_builds_draft_for_new_book(self, ask_title, ask_isbn, ask_price):
        draft = cli.book_fields(self.database)
        self.assertEqual(draft, BookDraft("New title", None, "8.00"))
        ask_title.assert_called_once_with("")
        ask_isbn.assert_called_once_with(self.database, "", exclude_id=None)
        ask_price.assert_called_once_with("")

    @patch("main.ask_title", return_value="Changed")
    def test_book_fields_stops_when_title_prompt_is_cancelled(self, ask_title):
        with patch("main.ask_title", return_value=None), patch("main.ask_isbn") as ask_isbn:
            self.assertIsNone(cli.book_fields(self.database))
        ask_isbn.assert_not_called()

    @patch("main.ask_price", return_value=None)
    @patch("main.ask_isbn", return_value=None)
    @patch("main.ask_title", return_value="Changed")
    def test_book_fields_stops_when_price_prompt_is_cancelled(self, ask_title, ask_isbn, ask_price):
        self.assertIsNone(cli.book_fields(self.database))
        ask_price.assert_called_once()

    @patch("main.ask_price", return_value=Decimal("20.00"))
    @patch("main.ask_isbn", return_value=None)
    @patch("main.ask_title", return_value="Changed")
    def test_book_fields_uses_existing_book_as_defaults_and_excludes_its_id(
        self, ask_title, ask_isbn, ask_price
    ):
        current = make_book(9, "Original", None, "4.00")
        cli.book_fields(self.database, current)
        ask_title.assert_called_once_with("Original")
        ask_isbn.assert_called_once_with(self.database, "", exclude_id=9)
        ask_price.assert_called_once_with("4.00")


class DisplayTests(unittest.TestCase):
    def test_show_book_table_renders_columns_and_book_values(self):
        output = StringIO()
        original_console = cli.console
        cli.console = Console(file=output, force_terminal=False, color_system=None)
        try:
            cli.show_book_table([make_book()], "BOOK RESULTS")
        finally:
            cli.console = original_console
        rendered = output.getvalue()
        for value in ("BOOK RESULTS", "ID", "Title", "ISBN", "Price", "Dune", "9780306406157", "₹12.50"):
            with self.subTest(value=value):
                self.assertIn(value, rendered)

    @patch("main.console.print")
    def test_show_book_table_explains_empty_result(self, print_message):
        cli.show_book_table([])
        print_message.assert_called_once_with("[yellow]No books found.[/]")

    @patch("main.console.print")
    @patch("main.console.clear")
    def test_show_header_clears_screen_and_shows_subtitle(self, clear, print_message):
        cli.show_header("BOOK MANAGEMENT")
        clear.assert_called_once_with()
        self.assertEqual(print_message.call_count, 2)
        self.assertIn("BOOK MANAGEMENT", print_message.call_args_list[1].args[0])


class BookActionTests(unittest.TestCase):
    def setUp(self):
        self.database = MagicMock()

    @patch("main.console.print")
    @patch("main.choose", return_value="Save book")
    @patch("main.save_new_book")
    @patch("main.show_book_table")
    @patch("main.book_fields", return_value=BookDraft("Dune", None, "10"))
    def test_add_book_previews_and_saves_book(self, fields, table, save, choose, print_message):
        cli.add_book(self.database)
        table.assert_called_once()
        self.assertEqual(table.call_args.args[1], "NEW BOOK")
        choose.assert_called_once_with("Save this book?", ["Save book", "Edit details", "Cancel"])
        save.assert_called_once_with(self.database, BookDraft("Dune", None, "10"))
        self.assertTrue(any("Book added successfully" in str(item) for item in print_message.call_args_list))

    @patch("main.console.print")
    @patch("main.choose", side_effect=["Edit details", "Save book"])
    @patch("main.save_new_book")
    @patch("main.show_book_table")
    @patch("main.book_fields", return_value=BookDraft("Dune", None, "10"))
    def test_add_book_can_edit_then_save(self, fields, table, save, choose, print_message):
        cli.add_book(self.database)
        self.assertEqual(fields.call_count, 2)
        self.assertEqual(fields.call_args_list[0], call(self.database, None))
        self.assertEqual(fields.call_args_list[1], call(self.database, ("Dune", "", "10.00")))
        save.assert_called_once()

    @patch("main.console.print")
    @patch("main.choose", return_value="Cancel")
    @patch("main.save_new_book")
    @patch("main.book_fields", return_value=BookDraft("Dune", None, "10"))
    def test_add_book_cancel_does_not_save(self, fields, save, choose, print_message):
        cli.add_book(self.database)
        save.assert_not_called()
        self.assertTrue(any("Adding book cancelled" in str(item) for item in print_message.call_args_list))

    @patch("main.console.print")
    @patch("main.choose", side_effect=["Save book", "Save book"])
    @patch("main.save_new_book", side_effect=[DuplicateISBN("duplicate"), None])
    @patch("main.book_fields", return_value=BookDraft("Dune", "9780306406157", "10"))
    def test_add_book_duplicate_isbn_returns_to_entry_with_existing_values(
        self, fields, save, choose, print_message
    ):
        cli.add_book(self.database)
        self.assertEqual(fields.call_count, 2)
        self.assertEqual(fields.call_args_list[1], call(self.database, ("Dune", "9780306406157", "10.00")))
        self.assertEqual(save.call_count, 2)

    @patch("main.read_books", return_value=[make_book()])
    @patch("main.show_book_table")
    @patch("main.text_input", return_value="  dune  ")
    def test_search_trims_query_and_displays_results(self, text_input, table, read_books):
        cli.search_books(self.database)
        read_books.assert_called_once_with(self.database, "dune")
        table.assert_called_once_with([make_book()])

    @patch("main.read_books")
    @patch("main.show_book_table")
    @patch("main.text_input", return_value=None)
    def test_search_cancel_does_not_query_or_display(self, text_input, table, read_books):
        cli.search_books(self.database)
        read_books.assert_not_called()
        table.assert_not_called()

    @patch("main.choose")
    @patch("main.read_books", return_value=[make_book(), make_book(2, "Foundation", None, "8")])
    @patch("main.text_input", return_value=" Dune ")
    def test_choose_book_searches_then_returns_selected_id(self, text_input, read_books, choose):
        choose.return_value = 2
        self.assertEqual(cli.choose_book(self.database), 2)
        read_books.assert_called_once_with(self.database, "Dune")
        self.assertEqual(choose.call_args.args[0], "Select a book")
        choices = choose.call_args.args[1]
        self.assertEqual([choice.value for choice in choices], [1, 2])

    @patch("main.console.print")
    @patch("main.read_books", return_value=[])
    @patch("main.text_input", return_value="missing")
    def test_choose_book_reports_no_matches(self, text_input, read_books, print_message):
        self.assertIsNone(cli.choose_book(self.database))
        print_message.assert_called_once()

    @patch("main.read_books")
    @patch("main.text_input", return_value=None)
    def test_choose_book_returns_on_escape(self, text_input, read_books):
        self.assertIsNone(cli.choose_book(self.database))
        read_books.assert_not_called()

    @patch("main.console.print")
    @patch("main.choose", return_value="Save changes")
    @patch("main.save_book_update")
    @patch("main.show_book_table")
    @patch("main.book_fields", return_value=BookDraft("Changed", None, "15"))
    @patch("main.read_book", return_value=make_book())
    @patch("main.choose_book", return_value=1)
    def test_update_prompts_edits_previews_and_saves(
        self, choose_book, read_book, fields, table, save, choose, print_message
    ):
        cli.update_book(self.database)
        choose_book.assert_called_once_with(self.database)
        read_book.assert_called_once_with(self.database, 1)
        fields.assert_called_once_with(self.database, make_book())
        save.assert_called_once_with(self.database, 1, BookDraft("Changed", None, "15"))
        self.assertEqual(table.call_args.args[1], "BOOK PREVIEW")

    @patch("main.console.print")
    @patch("main.choose", return_value="Cancel")
    @patch("main.save_book_update")
    @patch("main.book_fields", return_value=BookDraft("Changed", None, "15"))
    @patch("main.read_book", return_value=make_book())
    @patch("main.choose_book", return_value=1)
    def test_update_cancel_leaves_book_unchanged(
        self, choose_book, read_book, fields, save, choose, print_message
    ):
        cli.update_book(self.database)
        save.assert_not_called()

    @patch("main.console.print")
    @patch("main.choose", return_value="Save changes")
    @patch("main.save_book_update", side_effect=DuplicateISBN("duplicate"))
    @patch("main.book_fields", return_value=BookDraft("Changed", "9780306406157", "15"))
    @patch("main.read_book", return_value=make_book())
    @patch("main.choose_book", return_value=1)
    def test_update_duplicate_isbn_keeps_edit_flow_open(
        self, choose_book, read_book, fields, save, choose, print_message
    ):
        choose.side_effect = ["Save changes", "Cancel"]
        cli.update_book(self.database)
        self.assertEqual(fields.call_count, 2)
        self.assertEqual(fields.call_args_list[1], call(self.database, Book(1, "Changed", "9780306406157", Decimal("15.00"))))

    @patch("main.console.print")
    @patch("main.questionary.confirm")
    @patch("main.ask")
    @patch("main.show_book_table")
    @patch("main.remove_book")
    @patch("main.read_book", return_value=make_book())
    @patch("main.choose_book", return_value=1)
    def test_delete_confirms_before_removing(
        self, choose_book, read_book, remove, table, ask, confirm, print_message
    ):
        ask.return_value = True
        cli.delete_book(self.database)
        remove.assert_called_once_with(self.database, 1)
        self.assertEqual(ask.call_count, 1)

    @patch("main.console.print")
    @patch("main.questionary.confirm")
    @patch("main.ask", return_value=False)
    @patch("main.remove_book")
    @patch("main.read_book", return_value=make_book())
    @patch("main.choose_book", return_value=1)
    def test_delete_cancel_does_not_remove(
        self, choose_book, read_book, remove, ask, confirm, print_message
    ):
        cli.delete_book(self.database)
        remove.assert_not_called()

    @patch("main.console.print")
    @patch("main.remove_book")
    @patch("main.read_book", return_value=None)
    @patch("main.choose_book", return_value=1)
    def test_delete_handles_book_removed_after_selection(self, choose_book, read_book, remove, print_message):
        cli.delete_book(self.database)
        remove.assert_not_called()


class MenuAndApplicationTests(unittest.TestCase):
    def setUp(self):
        self.database = MagicMock()

    @patch("main.pause")
    @patch("main.search_books")
    @patch("main.read_books", return_value=[])
    @patch("main.show_book_table")
    @patch("main.show_header")
    @patch("main.choose", side_effect=["View all books", "Search books", "Back"])
    def test_manage_books_routes_menu_actions_and_returns_on_back(
        self, choose, show_header, table, read_books, search, pause
    ):
        cli.manage_books(self.database)
        self.assertEqual(choose.call_count, 3)
        table.assert_called_once_with([])
        search.assert_called_once_with(self.database)
        self.assertEqual(pause.call_count, 2)

    @patch("main.pause")
    @patch("main.show_header")
    @patch("main.choose", return_value=None)
    def test_manage_books_returns_on_escape(self, choose, show_header, pause):
        cli.manage_books(self.database)
        pause.assert_not_called()

    @patch("main.console.print")
    @patch("main.ask", side_effect=[False, True])
    @patch("main.choose", side_effect=["Exit", "Exit"])
    @patch("main.show_header")
    @patch("main.questionary.confirm")
    @patch("main.connect_database")
    def test_main_requires_exit_confirmation_and_closes_database(
        self, connect, confirm, show_header, choose, ask, print_message
    ):
        connect.return_value = self.database
        cli.main()
        self.assertEqual(ask.call_count, 2)
        self.assertEqual(confirm.call_count, 2)
        self.database.close.assert_called_once_with()

    @patch("main.console.print")
    @patch("main.ask", return_value=False)
    @patch("main.show_header")
    @patch("main.questionary.confirm")
    @patch("main.connect_database", side_effect=PersistenceError("offline"))
    def test_main_can_decline_connection_retry(
        self, connect, confirm, show_header, ask, print_message
    ):
        cli.main()
        connect.assert_called_once_with()
        ask.assert_called_once()
        confirm.assert_called_once()

    @patch("main.console.print")
    @patch("main.pause")
    @patch("main.read_books", side_effect=PersistenceError("query failed"))
    @patch("main.manage_books")
    @patch("main.choose", return_value="Manage books")
    @patch("main.show_header")
    @patch("main.connect_database")
    def test_main_reports_runtime_database_error_and_closes_database(
        self, connect, show_header, choose, manage_books, read_books, pause, print_message
    ):
        connect.return_value = self.database
        manage_books.side_effect = PersistenceError("query failed")
        cli.main()
        self.database.close.assert_called_once_with()
        pause.assert_called_once_with()
        self.assertTrue(any("Database error" in str(item) for item in print_message.call_args_list))


if __name__ == "__main__":
    unittest.main()
