# Home Library Specification

## Goal

Allow one person to keep a digital record of the books they own at home. The
program provides a small terminal interface for adding, viewing, finding,
editing, and removing books from a MySQL database.

The first phase focuses on a simple, working book catalogue. It does not track
authors, loans, physical shelf locations, or multiple copies.

## Book data and lifecycle

Each book has a generated integer ID, title, ISBN, and price in Indian rupees.
The title is required and may contain at most 200 characters. ISBN is required,
must be a valid ISBN-10 or ISBN-13, and must be unique in the collection. Spaces
and hyphens in entered ISBN values are ignored. Price is required, non-negative,
and may have at most two decimal places.

Users can add a book, list all books, search by title or ISBN, update a selected
book, and delete a selected book after confirmation. Changes are stored in MySQL
and remain available after the program exits.

## Interface

The application runs in a terminal and uses Rich for headings, messages, and
aligned book tables. Menus use arrow keys to move, Enter to select, and Escape
to return to the previous menu or cancel the current form. The main menu opens
book management or exits the program. Book management offers add, view, search,
update, delete, and back actions.

Adding and updating show a preview before saving. Users can choose to save,
revise the entered details, or cancel. Deleting displays the selected book and
requires an explicit yes/no confirmation. Search accepts part of a title or
ISBN; a blank search in the search screen displays all books.

## Storage

The application connects to the MySQL service defined in `compose.yaml`. It
creates the `home_library` database and `books` table when they do not exist.
The `books` table has these fields:

| Field | Type | Rules |
| --- | --- | --- |
| `id` | `INT` | Primary key, auto-increment |
| `title` | `VARCHAR(200)` | Required |
| `isbn` | `VARCHAR(13)` | Required, unique |
| `price` | `DECIMAL(10, 2)` | Required, zero or greater |

The MySQL service stores its data in a named Docker volume. Connection values
can be supplied through `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, and
`MYSQL_PASSWORD`; local defaults support the included Compose setup.

## Operation

Use `uv sync` to install the Python dependencies and `docker compose up -d mysql`
to start the database. Run the program with `uv run main.py`. The containerized
application can also be started with `docker compose up --build app`.

The project targets Python 3.12 or newer. The terminal must support interactive
keyboard input and Unicode characters used by the interface.

## Out of scope

- Author records or linking books to authors
- Multiple copies, lending, returns, or borrower records
- Physical location, categories, ratings, or notes
- Multiple user accounts, roles, or network access controls
- A graphical or web interface
- Reports, exports, or synchronization with external book services

## Acceptance criteria

- The program starts and connects to the included MySQL Compose service.
- Users can add a book with a valid unique ISBN and a non-negative price.
- Invalid or duplicate ISBN values, empty titles, and invalid prices are rejected
  before a database write.
- All books display in an aligned table with ID, title, ISBN, and price.
- Search returns books matching part of their title or ISBN.
- Users can find a book, update its details, and save the changes.
- A book is deleted only after explicit confirmation.
- Arrow-key navigation, Enter selection, and Escape back/cancel work in menus
  and input prompts.
- Records persist in MySQL after exiting and restarting the program.
