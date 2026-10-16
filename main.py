import os
import re
from decimal import Decimal, InvalidOperation

import mysql.connector
import questionary
from mysql.connector import Error
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.keys import Keys
from questionary import Choice, Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()
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
            "[bold cyan]◆ HOME LIBRARY[/]\n[dim]Personal Book Catalogue[/]",
            border_style="cyan",
            expand=False,
        )
    )
    console.print(f"[bold]{subtitle}[/]\n")


def pause():
    console.input("\n[dim]Press Enter to continue...[/]")


def connect_database():
    database = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "schoolproject"),
    )
    cursor = database.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS home_library")
    cursor.execute("USE home_library")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS books ("
        "id INT AUTO_INCREMENT PRIMARY KEY, "
        "title VARCHAR(200) NOT NULL, "
        "isbn VARCHAR(13) NOT NULL UNIQUE, "
        "price DECIMAL(10, 2) NOT NULL, "
        "CHECK (price >= 0))"
    )
    cursor.close()
    return database


def normalize_isbn(value):
    isbn = re.sub(r"[\s-]", "", value).upper()
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
    return None


def ask_title(default=""):
    while True:
        title = text_input("Book title", default)
        if title is None:
            return None
        title = title.strip()
        if title:
            if len(title) > 200:
                console.print("[bold red]Title must be 200 characters or fewer.[/]")
                continue
            return title
        console.print("[bold red]Title cannot be empty.[/]")


def ask_isbn(database, default="", exclude_id=None):
    while True:
        value = text_input("ISBN-10 or ISBN-13", default)
        if value is None:
            return None
        isbn = normalize_isbn(value)
        if isbn is None:
            console.print("[bold red]Enter a valid ISBN-10 or ISBN-13.[/]")
            default = value
            continue
        cursor = database.cursor()
        if exclude_id is None:
            cursor.execute("SELECT id FROM books WHERE isbn = %s", (isbn,))
        else:
            cursor.execute(
                "SELECT id FROM books WHERE isbn = %s AND id <> %s",
                (isbn, exclude_id),
            )
        duplicate = cursor.fetchone()
        cursor.close()
        if duplicate:
            console.print("[bold red]That ISBN is already in your collection.[/]")
            default = value
            continue
        return isbn


def ask_price(default=""):
    while True:
        value = text_input("Price in INR", default)
        if value is None:
            return None
        if not re.fullmatch(r"\d+(\.\d{1,2})?", value.strip()):
            console.print("[bold red]Enter a non-negative price with at most 2 decimal places.[/]")
            default = value
            continue
        try:
            price = Decimal(value.strip())
        except InvalidOperation:
            console.print("[bold red]Enter a valid price.[/]")
            default = value
            continue
        if price > Decimal("99999999.99"):
            console.print("[bold red]Price must be less than ₹100,000,000.[/]")
            default = value
            continue
        return price.quantize(Decimal("0.01"))


def book_fields(database, current=None):
    current = current or ("", "", "")
    book_id = current[0] if len(current) == 4 else None
    title = ask_title(current[1] if len(current) == 4 else "")
    if title is None:
        return None
    isbn = ask_isbn(
        database,
        current[2] if len(current) == 4 else "",
        exclude_id=book_id,
    )
    if isbn is None:
        return None
    price = ask_price(str(current[3]) if len(current) == 4 else "")
    if price is None:
        return None
    return title, isbn, price


def show_book_table(books, title="BOOKS"):
    if not books:
        console.print("[yellow]No books found.[/]")
        return
    table = Table(title=title, header_style="bold cyan", show_lines=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="white")
    table.add_column("ISBN", style="green")
    table.add_column("Price", style="yellow", justify="right")
    for book_id, book_title, isbn, price in books:
        table.add_row(str(book_id), book_title, isbn, f"₹{price:.2f}")
    console.print(table)


def get_books(database, search=None):
    cursor = database.cursor()
    if search:
        pattern = f"%{search}%"
        cursor.execute(
            "SELECT id, title, isbn, price FROM books "
            "WHERE title LIKE %s OR isbn LIKE %s ORDER BY title",
            (pattern, pattern),
        )
    else:
        cursor.execute("SELECT id, title, isbn, price FROM books ORDER BY title")
    books = cursor.fetchall()
    cursor.close()
    return books


def add_book(database):
    current = None
    while True:
        fields = book_fields(database, current)
        if fields is None:
            console.print("[yellow]Adding book cancelled.[/]")
            return
        title, isbn, price = fields
        show_book_table([(0, title, isbn, price)], "NEW BOOK")
        action = choose("Save this book?", ["Save book", "Edit details", "Cancel"])
        if action == "Save book":
            cursor = database.cursor()
            cursor.execute(
                "INSERT INTO books (title, isbn, price) VALUES (%s, %s, %s)",
                (title, isbn, price),
            )
            database.commit()
            cursor.close()
            console.print("[bold green]Book added successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Adding book cancelled.[/]")
            return
        current = (None, title, isbn, price)


def search_books(database):
    search = text_input("Search by title or ISBN (leave blank to show all)")
    if search is None:
        return
    show_book_table(get_books(database, search.strip()))


def choose_book(database):
    search = text_input("Find a book by title or ISBN")
    if search is None:
        return None
    books = get_books(database, search.strip())
    if not books:
        console.print("[yellow]No matching books found.[/]")
        return None
    choices = [
        Choice(
            f"{title}  ·  {isbn}  ·  ₹{price:.2f}",
            value=book_id,
        )
        for book_id, title, isbn, price in books
    ]
    return choose("Select a book", choices)


def update_book(database):
    book_id = choose_book(database)
    if book_id is None:
        return
    cursor = database.cursor()
    cursor.execute("SELECT id, title, isbn, price FROM books WHERE id = %s", (book_id,))
    old_book = cursor.fetchone()
    cursor.close()
    while True:
        fields = book_fields(database, old_book)
        if fields is None:
            console.print("[yellow]Update cancelled.[/]")
            return
        title, isbn, price = fields
        console.print("\n[bold]Updated details[/]")
        show_book_table([(book_id, title, isbn, price)], "BOOK PREVIEW")
        action = choose("Save these changes?", ["Save changes", "Edit details", "Cancel"])
        if action == "Save changes":
            cursor = database.cursor()
            cursor.execute(
                "UPDATE books SET title = %s, isbn = %s, price = %s WHERE id = %s",
                (title, isbn, price, book_id),
            )
            database.commit()
            cursor.close()
            console.print("[bold green]Book updated successfully.[/]")
            return
        if action != "Edit details":
            console.print("[yellow]Update cancelled.[/]")
            return
        old_book = (book_id, title, isbn, price)


def delete_book(database):
    book_id = choose_book(database)
    if book_id is None:
        return
    cursor = database.cursor()
    cursor.execute("SELECT id, title, isbn, price FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    show_book_table([book], "DELETE BOOK")
    confirmed = ask(questionary.confirm("Delete this book?", default=False, style=question_style))
    if confirmed:
        cursor = database.cursor()
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        database.commit()
        cursor.close()
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
            show_book_table(get_books(database))
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
        except Error as error:
            show_header("DATABASE CONNECTION")
            console.print(f"[bold red]Could not connect to MySQL:[/] {error}")
            retry = ask(questionary.confirm("Retry connection?", default=False, style=question_style))
            if not retry:
                return

    try:
        while True:
            show_header("MAIN MENU")
            action = choose("Choose an action", ["Manage books", "Exit"])
            if action == "Manage books":
                manage_books(database)
            elif action == "Exit" or action is None:
                if ask(questionary.confirm("Exit the library?", default=False, style=question_style)):
                    break
    except Error as error:
        console.print(f"[bold red]Database error:[/] {error}")
        pause()
    finally:
        database.close()


if __name__ == "__main__":
    main()
