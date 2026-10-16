import questionary
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.keys import Keys
from questionary import Choice, Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from home_library import use_cases
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
from home_library.persistence import PersistenceError, connect_database


console = Console()
CANCELLED = object()
question_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("instruction", "fg:ansigray"),
        ("validation-toolbar", "fg:red"),
    ]
)


def ask(question):
    escape_bindings = KeyBindings()

    @escape_bindings.add(Keys.Escape, eager=True)
    def cancel(event):
        event.app.exit(result=None)

    question.application.key_bindings = merge_key_bindings(
        [question.application.key_bindings, escape_bindings]
    )
    return question.ask(kbi_msg="")


def choose(message, choices):
    return ask(
        questionary.select(
            message,
            choices=choices,
            qmark="❯",
            pointer="▶",
            instruction="(↑/↓ move, Enter select, Esc back)",
            use_jk_keys=False,
            use_emacs_keys=False,
            style=question_style,
        )
    )


def text_input(message, default=""):
    return ask(questionary.text(message, default=default, style=question_style))


def show_header(subtitle):
    console.clear()
    console.print(
        Panel(
            "[bold cyan]◆ HOME LIBRARY[/]\n[dim]Family Reading Catalogue[/]",
            border_style="cyan",
            expand=False,
        )
    )
    console.print(f"[bold]{subtitle}[/]\n")


def pause():
    console.input("\n[dim]Press Enter to continue...[/]")


def read_books(database, search=""):
    with database.unit_of_work() as unit_of_work:
        return use_cases.get_books(unit_of_work, search)


def read_book(database, book_id):
    with database.unit_of_work() as unit_of_work:
        return use_cases.find_book(unit_of_work, book_id)


def isbn_conflict(database, isbn, exclude_id=None):
    with database.unit_of_work() as unit_of_work:
        return use_cases.find_isbn_conflict(unit_of_work, isbn, exclude_id)


def ask_title(default=""):
    while True:
        value = text_input("Book title", default)
        if value is None:
            return None
        try:
            return validate_title(value)
        except InvalidTitle as error:
            console.print(f"[bold red]{error}[/]")
            default = value


def ask_isbn(database, default="", exclude_id=None):
    while True:
        value = text_input("ISBN-10 or ISBN-13 (optional)", default)
        if value is None:
            return CANCELLED
        try:
            isbn = normalize_isbn(value)
        except InvalidISBN as error:
            console.print(f"[bold red]{error}[/]")
            default = value
            continue
        if isbn and isbn_conflict(database, isbn, exclude_id):
            console.print("[bold red]That ISBN is already in your collection.[/]")
            default = value
            continue
        return isbn


def ask_price(default=""):
    while True:
        value = text_input("Price in INR", default)
        if value is None:
            return None
        try:
            return parse_price(value)
        except InvalidPrice as error:
            console.print(f"[bold red]{error}[/]")
            default = value


def book_fields(database, current=None):
    if isinstance(current, Book):
        defaults = (current.title, current.isbn or "", str(current.price))
        book_id = current.id
    elif current:
        defaults = current
        book_id = None
    else:
        defaults = ("", "", "")
        book_id = None
    title = ask_title(defaults[0])
    if title is None:
        return None
    isbn = ask_isbn(database, defaults[1], exclude_id=book_id)
    if isbn is CANCELLED:
        return None
    price = ask_price(defaults[2])
    if price is None:
        return None
    return BookDraft(title, isbn, price)


def show_book_table(books, title="BOOKS"):
    if not books:
        console.print("[yellow]No books found.[/]")
        return
    table = Table(title=title, header_style="bold cyan", show_lines=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="white")
    table.add_column("ISBN", style="green")
    table.add_column("Price", style="yellow", justify="right")
    for book in books:
        table.add_row(
            str(book.id),
            book.title,
            book.isbn or "—",
            f"₹{book.price:.2f}",
        )
    console.print(table)


def save_new_book(database, draft):
    with database.unit_of_work() as unit_of_work:
        book = use_cases.create_book(unit_of_work, draft)
        unit_of_work.commit()
        return book


def save_book_update(database, book_id, draft):
    with database.unit_of_work() as unit_of_work:
        book = use_cases.update_book(unit_of_work, book_id, draft)
        unit_of_work.commit()
        return book


def remove_book(database, book_id):
    with database.unit_of_work() as unit_of_work:
        use_cases.delete_book(unit_of_work, book_id)
        unit_of_work.commit()


def add_book(database):
    current = None
    while True:
        draft = book_fields(database, current)
        if draft is None:
            console.print("[yellow]Adding book cancelled.[/]")
            return
        show_book_table([Book(0, draft.title, draft.isbn, draft.price)], "NEW BOOK")
        action = choose("Save this book?", ["Save book", "Edit details", "Cancel"])
        if action == "Save book":
            try:
                save_new_book(database, draft)
            except use_cases.DuplicateISBN as error:
                console.print(f"[bold red]{error}[/]")
                current = (draft.title, draft.isbn or "", str(draft.price))
                continue
            console.print("[bold green]Book added successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Adding book cancelled.[/]")
            return
        current = (draft.title, draft.isbn or "", str(draft.price))


def search_books(database):
    search = text_input("Search by title or ISBN (leave blank to show all)")
    if search is None:
        return
    show_book_table(read_books(database, search.strip()))


def choose_book(database):
    search = text_input("Find a book by title or ISBN")
    if search is None:
        return None
    books = read_books(database, search.strip())
    if not books:
        console.print("[yellow]No matching books found.[/]")
        return None
    choices = [
        Choice(
            f"{book.title}  ·  {book.isbn or 'No ISBN'}  ·  ₹{book.price:.2f}",
            value=book.id,
        )
        for book in books
    ]
    return choose("Select a book", choices)


def update_book(database):
    book_id = choose_book(database)
    if book_id is None:
        return
    old_book = read_book(database, book_id)
    while old_book:
        draft = book_fields(database, old_book)
        if draft is None:
            console.print("[yellow]Update cancelled.[/]")
            return
        preview = Book(book_id, draft.title, draft.isbn, draft.price)
        console.print("\n[bold]Updated details[/]")
        show_book_table([preview], "BOOK PREVIEW")
        action = choose("Save these changes?", ["Save changes", "Edit details", "Cancel"])
        if action == "Save changes":
            try:
                save_book_update(database, book_id, draft)
            except use_cases.DuplicateISBN as error:
                console.print(f"[bold red]{error}[/]")
                old_book = preview
                continue
            console.print("[bold green]Book updated successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Update cancelled.[/]")
            return
        old_book = preview


def delete_book(database):
    book_id = choose_book(database)
    if book_id is None:
        return
    book = read_book(database, book_id)
    if book is None:
        console.print("[yellow]That book no longer exists.[/]")
        return
    show_book_table([book], "DELETE BOOK")
    confirmed = ask(
        questionary.confirm("Delete this book?", default=False, style=question_style)
    )
    if confirmed:
        remove_book(database, book_id)
        console.print("[bold green]Book deleted successfully.[/]")
    else:
        console.print("[yellow]Deletion cancelled.[/]")


def manage_books(database):
    while True:
        show_header("BOOK MANAGEMENT")
        action = choose(
            "Choose an action",
            [
                "Add book",
                "View all books",
                "Search books",
                "Update book",
                "Delete book",
                "Back",
            ],
        )
        if action is None or action == "Back":
            return
        if action == "Add book":
            add_book(database)
        elif action == "View all books":
            show_book_table(read_books(database))
        elif action == "Search books":
            search_books(database)
        elif action == "Update book":
            update_book(database)
        elif action == "Delete book":
            delete_book(database)
        pause()


def main():
    while True:
        try:
            database = connect_database()
            break
        except PersistenceError as error:
            show_header("DATABASE CONNECTION")
            console.print(f"[bold red]{error}[/]")
            retry = ask(
                questionary.confirm(
                    "Retry connection?", default=False, style=question_style
                )
            )
            if not retry:
                return

    try:
        while True:
            show_header("MAIN MENU")
            action = choose("Choose an action", ["Manage books", "Exit"])
            if action == "Manage books":
                manage_books(database)
            elif action == "Exit" or action is None:
                if ask(
                    questionary.confirm(
                        "Exit the library?", default=False, style=question_style
                    )
                ):
                    break
    except PersistenceError as error:
        console.print(f"[bold red]Database error:[/] {error}")
        pause()
    finally:
        database.close()


if __name__ == "__main__":
    main()
