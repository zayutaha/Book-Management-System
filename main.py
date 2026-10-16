import questionary
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style as PromptStyle
from questionary import Choice, Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from home_library import use_cases
from home_library.domain import (
    Author,
    AuthorBookGroup,
    AuthorDraft,
    Book,
    BookDraft,
    InvalidAuthorName,
    InvalidBirthDate,
    InvalidISBN,
    InvalidPrice,
    InvalidTitle,
    normalize_isbn,
    parse_birth_date,
    parse_price,
    validate_author_name,
    validate_title,
)
from home_library.persistence import PersistenceError, connect_database


console = Console()
CANCELLED = object()
ADD_AUTHOR = object()
SEARCH_AGAIN = object()
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
        return use_cases.books.get_books(unit_of_work, search)


def read_book(database, book_id):
    with database.unit_of_work() as unit_of_work:
        return use_cases.books.find_book(unit_of_work, book_id)


def read_authors(database, search=""):
    with database.unit_of_work() as unit_of_work:
        return use_cases.authors.get_authors(unit_of_work, search)


def read_author(database, author_id):
    with database.unit_of_work() as unit_of_work:
        return use_cases.authors.find_author(unit_of_work, author_id)


def read_grouped_books(database):
    with database.unit_of_work() as unit_of_work:
        return use_cases.authors.get_books_grouped_by_author(unit_of_work)


def isbn_conflict(database, isbn, exclude_id=None):
    with database.unit_of_work() as unit_of_work:
        return use_cases.books.find_isbn_conflict(unit_of_work, isbn, exclude_id)


def author_name_conflict(database, name, exclude_id=None):
    with database.unit_of_work() as unit_of_work:
        return use_cases.authors.author_name_conflict(unit_of_work, name, exclude_id)


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


def ask_author_name(database, default="", exclude_id=None):
    while True:
        value = text_input("Author name", default)
        if value is None:
            return None
        try:
            name = validate_author_name(value)
        except InvalidAuthorName as error:
            console.print(f"[bold red]{error}[/]")
            default = value
            continue
        if author_name_conflict(database, name, exclude_id):
            console.print("[bold red]An author with that name already exists.[/]")
            default = value
            continue
        return name


def ask_birth_date(default=""):
    while True:
        value = text_input("Date of birth (YYYY-MM-DD)", default)
        if value is None:
            return None
        try:
            return parse_birth_date(value)
        except InvalidBirthDate as error:
            console.print(f"[bold red]{error}[/]")
            default = value


def author_fields(database, current=None):
    name_default = current.name if isinstance(current, (Author, AuthorDraft)) else ""
    date_default = current.birth_date.isoformat() if isinstance(current, (Author, AuthorDraft)) else ""
    current_id = current.id if isinstance(current, Author) else None
    name = ask_author_name(database, name_default, current_id)
    if name is None:
        return None
    birth_date = ask_birth_date(date_default)
    if birth_date is None:
        return None
    return AuthorDraft(name, birth_date)


def book_fields(database, current=None):
    if isinstance(current, Book):
        defaults = (current.title, current.isbn or "", str(current.price))
        author_id = current.author_id
        book_id = current.id
    elif current:
        defaults = current[:3]
        author_id = current[3] if len(current) > 3 else None
        book_id = None
    else:
        defaults = ("", "", "")
        author_id = None
        book_id = None

    while True:
        title = ask_title(defaults[0])
        if title is None:
            return None
        isbn = ask_isbn(database, defaults[1], exclude_id=book_id)
        if isbn is CANCELLED:
            return None
        price = ask_price(defaults[2])
        if price is None:
            return None
        selected_author_id = choose_author(database, selected_id=author_id)
        if selected_author_id is CANCELLED:
            defaults = (title, isbn or "", str(price))
            continue
        return BookDraft(title, isbn, price, selected_author_id)


def show_book_table(books, title="BOOKS"):
    if not books:
        console.print("[yellow]No books found.[/]")
        return
    table = Table(title=title, header_style="bold cyan", show_lines=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="white")
    table.add_column("Author", style="magenta")
    table.add_column("ISBN", style="green")
    table.add_column("Price", style="yellow", justify="right")
    for book in books:
        table.add_row(
            str(book.id),
            book.title,
            book.author_name,
            book.isbn or "—",
            f"₹{book.price:.2f}",
        )
    console.print(table)


def show_author_table(authors, title="AUTHORS"):
    if not authors:
        console.print("[yellow]No authors found.[/]")
        return
    table = Table(title=title, header_style="bold cyan", show_lines=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Date of birth", style="green")
    table.add_column("Books", style="yellow", justify="right")
    for author in authors:
        table.add_row(
            str(author.id),
            author.name,
            author.birth_date.isoformat(),
            str(author.book_count),
        )
    console.print(table)


def save_new_book(database, draft):
    with database.unit_of_work() as unit_of_work:
        book = use_cases.books.create_book(unit_of_work, draft)
        unit_of_work.commit()
        return book


def save_book_update(database, book_id, draft):
    with database.unit_of_work() as unit_of_work:
        book = use_cases.books.update_book(unit_of_work, book_id, draft)
        unit_of_work.commit()
        return book


def remove_book(database, book_id):
    with database.unit_of_work() as unit_of_work:
        use_cases.books.delete_book(unit_of_work, book_id)
        unit_of_work.commit()


def save_new_author(database, draft):
    with database.unit_of_work() as unit_of_work:
        author = use_cases.authors.create_author(unit_of_work, draft)
        unit_of_work.commit()
        return author


def save_author_update(database, author_id, draft):
    with database.unit_of_work() as unit_of_work:
        author = use_cases.authors.update_author(unit_of_work, author_id, draft)
        unit_of_work.commit()
        return author


def add_author(database, return_author=False):
    current = None
    while True:
        draft = author_fields(database, current)
        if draft is None:
            if not return_author:
                console.print("[yellow]Adding author cancelled.[/]")
            return None
        show_author_table([Author(0, draft.name, draft.birth_date, 0)], "NEW AUTHOR")
        action = choose("Save this author?", ["Save author", "Edit details", "Cancel"])
        if action == "Save author":
            try:
                author = save_new_author(database, draft)
            except use_cases.authors.DuplicateAuthorName as error:
                console.print(f"[bold red]{error}[/]")
                current = draft
                continue
            console.print("[bold green]Author added successfully.[/]")
            return author
        if action != "Edit details":
            if not return_author:
                console.print("[yellow]Adding author cancelled.[/]")
            return None
        current = draft


def choose_author(database, selected_id=None, include_add=True):
    selected_author = read_author(database, selected_id) if selected_id else None
    default_search = selected_author.name if selected_author else ""
    while True:
        search = text_input("Search authors by name", default_search)
        if search is None:
            return CANCELLED
        authors = read_authors(database, search.strip())
        if not authors:
            console.print("[yellow]No matching authors found.[/]")
            if not include_add:
                continue
            action = choose("No matching author", ["Add author", "Search again", "Cancel"])
            if action == "Add author":
                author = add_author(database, return_author=True)
                return author.id if author else CANCELLED
            if action == "Cancel" or action is None:
                return CANCELLED
            default_search = ""
            continue

        choices = [
            Choice(
                f"{author.name} · born {author.birth_date.isoformat()} · "
                f"{author.book_count} books",
                value=author.id,
            )
            for author in authors
        ]
        if include_add:
            choices.append(Choice("＋ Add author", value=ADD_AUTHOR))
        choices.append(Choice("Search again", value=SEARCH_AGAIN))
        selected = choose("Select an author", choices)
        if selected is None:
            return CANCELLED
        if selected is ADD_AUTHOR:
            author = add_author(database, return_author=True)
            return author.id if author else CANCELLED
        if selected is SEARCH_AGAIN:
            default_search = ""
            continue
        return selected


def add_book(database):
    current = None
    while True:
        draft = book_fields(database, current)
        if draft is None:
            console.print("[yellow]Adding book cancelled.[/]")
            return
        author = read_author(database, draft.author_id)
        show_book_table(
            [Book(0, draft.title, draft.isbn, draft.price, draft.author_id, author.name)],
            "NEW BOOK",
        )
        action = choose("Save this book?", ["Save book", "Edit details", "Cancel"])
        if action == "Save book":
            try:
                save_new_book(database, draft)
            except use_cases.books.DuplicateISBN as error:
                console.print(f"[bold red]{error}[/]")
                current = (draft.title, draft.isbn or "", str(draft.price), draft.author_id)
                continue
            console.print("[bold green]Book added successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Adding book cancelled.[/]")
            return
        current = (draft.title, draft.isbn or "", str(draft.price), draft.author_id)


def search_books(database):
    search = text_input("Search by title, ISBN, or author (leave blank to show all)")
    if search is None:
        return
    show_book_table(read_books(database, search.strip()))


def search_authors(database):
    search = text_input("Search authors by name (leave blank to show all)")
    if search is None:
        return
    show_author_table(read_authors(database, search.strip()))


def choose_book(database):
    search = text_input("Find a book by title, ISBN, or author")
    if search is None:
        return None
    books = read_books(database, search.strip())
    if not books:
        console.print("[yellow]No matching books found.[/]")
        return None
    choices = [
        Choice(
            f"{book.title} · {book.author_name} · {book.isbn or 'No ISBN'} · "
            f"₹{book.price:.2f}",
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
        author = read_author(database, draft.author_id)
        if author is None:
            console.print("[yellow]That author no longer exists.[/]")
            return
        preview = Book(
            book_id,
            draft.title,
            draft.isbn,
            draft.price,
            draft.author_id,
            author.name,
        )
        console.print("\n[bold]Updated details[/]")
        show_book_table([preview], "BOOK PREVIEW")
        action = choose("Save these changes?", ["Save changes", "Edit details", "Cancel"])
        if action == "Save changes":
            try:
                save_book_update(database, book_id, draft)
            except use_cases.books.DuplicateISBN as error:
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


def update_author(database):
    author_id = choose_author(database, include_add=False)
    if author_id is CANCELLED:
        return
    author = read_author(database, author_id)
    while author:
        draft = author_fields(database, author)
        if draft is None:
            console.print("[yellow]Update cancelled.[/]")
            return
        preview = Author(author_id, draft.name, draft.birth_date, author.book_count)
        show_author_table([preview], "AUTHOR PREVIEW")
        action = choose("Save these changes?", ["Save changes", "Edit details", "Cancel"])
        if action == "Save changes":
            try:
                save_author_update(database, author_id, draft)
            except use_cases.authors.DuplicateAuthorName as error:
                console.print(f"[bold red]{error}[/]")
                author = preview
                continue
            console.print("[bold green]Author updated successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Update cancelled.[/]")
            return
        author = preview


class GroupedBookNavigator:
    def __init__(self, groups):
        self.groups = groups
        self.selected = 0
        self.expanded = None

    def move(self, amount):
        if self.groups:
            next_selected = (self.selected + amount) % len(self.groups)
            if next_selected != self.selected:
                self.expanded = None
            self.selected = next_selected

    def expand(self):
        self.expanded = self.selected

    def collapse(self):
        if self.expanded == self.selected:
            self.expanded = None

    def toggle(self):
        if self.expanded == self.selected:
            self.expanded = None
        else:
            self.expanded = self.selected

    def render(self):
        lines = FormattedText(
            [
                ("class:title", "BOOKS BY AUTHOR\n"),
                ("class:help", "↑/↓ move  Enter/right expand  Enter/left collapse  Esc back\n\n"),
            ]
        )
        for index, group in enumerate(self.groups):
            selected = index == self.selected
            expanded = index == self.expanded
            marker = "▾" if expanded else "▸"
            style = "class:selected" if selected else "class:author"
            lines.append((style, f"{marker} {group.author.name}"))
            lines.append(("class:count", f"  ·  {group.author.birth_date.isoformat()}  ·  {group.author.book_count} books\n"))
            if expanded:
                if group.books:
                    for book in group.books:
                        lines.append(("class:book", f"    • {book.title}\n"))
                else:
                    lines.append(("class:empty", "    No books for this author yet.\n"))
        return lines


def run_grouped_book_navigator(groups):
    navigator = GroupedBookNavigator(groups)
    bindings = KeyBindings()

    @bindings.add(Keys.Up)
    def move_up(event):
        navigator.move(-1)
        event.app.invalidate()

    @bindings.add(Keys.Down)
    def move_down(event):
        navigator.move(1)
        event.app.invalidate()

    @bindings.add(Keys.Right)
    def expand(event):
        navigator.expand()
        event.app.invalidate()

    @bindings.add(Keys.Left)
    def collapse(event):
        navigator.collapse()
        event.app.invalidate()

    @bindings.add(Keys.Enter)
    def toggle(event):
        navigator.toggle()
        event.app.invalidate()

    @bindings.add(Keys.Escape, eager=True)
    def back(event):
        event.app.exit(result=None)

    application = Application(
        layout=Layout(Window(FormattedTextControl(navigator.render), wrap_lines=False)),
        key_bindings=bindings,
        style=PromptStyle.from_dict(
            {
                "title": "bold #00d7ff",
                "help": "#888888",
                "selected": "bold #00d7ff",
                "author": "#ffffff",
                "count": "#888888",
                "book": "#dddddd",
                "empty": "italic #888888",
            }
        ),
        full_screen=True,
    )
    application.run()


def show_grouped_books(database):
    groups = read_grouped_books(database)
    if not groups:
        console.print("[yellow]No authors found.[/]")
        return
    run_grouped_book_navigator(groups)


def manage_books(database):
    while True:
        show_header("BOOK MANAGEMENT")
        action = choose(
            "Choose an action",
            [
                "Add book",
                "View all books",
                "Search books",
                "Group books by author",
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
        elif action == "Group books by author":
            show_grouped_books(database)
        elif action == "Update book":
            update_book(database)
        elif action == "Delete book":
            delete_book(database)
        pause()


def manage_authors(database):
    while True:
        show_header("AUTHOR MANAGEMENT")
        action = choose(
            "Choose an action",
            ["Add author", "View all authors", "Search authors", "Update author", "Back"],
        )
        if action is None or action == "Back":
            return
        if action == "Add author":
            add_author(database)
        elif action == "View all authors":
            show_author_table(read_authors(database))
        elif action == "Search authors":
            search_authors(database)
        elif action == "Update author":
            update_author(database)
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
            action = choose("Choose an action", ["Manage books", "Manage authors", "Exit"])
            if action == "Manage books":
                manage_books(database)
            elif action == "Manage authors":
                manage_authors(database)
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
