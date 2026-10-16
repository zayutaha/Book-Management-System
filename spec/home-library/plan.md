# Home Library Technical Implementation Plan

## Architecture

Keep `main.py` as the Rich and Questionary interface adapter. Put book data and
rules in `home_library/domain`, book workflows in `home_library/use_cases`, and
MySQL setup and SQL in `home_library/persistence`. The separate
[`layered-architecture/spec.md`](layered-architecture/spec.md) defines these
boundaries. Docker Compose runs MySQL 8.4 with a persistent named volume; `uv`
manages the Python environment.

```text
Rich / Questionary interface -> use cases -> persistence -> MySQL
                                      |          |
                                      +-> domain <-+
```

## Data model

Create two tables in `home_library`:

| Table | Field | Type and constraints |
| --- | --- | --- |
| `authors` | `id` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `authors` | `name` | `VARCHAR(200) NOT NULL UNIQUE` |
| `books` | `id` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `books` | `title` | `VARCHAR(200) NOT NULL` |
| `books` | `author_id` | `INT NOT NULL`, foreign key to `authors.id` |
| `books` | `isbn` | `VARCHAR(13) NULL UNIQUE` |
| `books` | `price` | `DECIMAL(10, 2) NOT NULL`, zero or greater |

One author can have many books; each book has one author. Use `ON DELETE
RESTRICT` so an author with linked books cannot be removed accidentally. Keep
book IDs stable when adding the relation. Add the author table and `author_id`
with a migration that preserves existing books; assign existing books to an
explicit placeholder author such as `Unknown` before making the foreign key
required. Do not silently discard current records.

## Author workflows

Author Management provides add, list, update, and delete actions. Author names
are trimmed, required, limited to 200 characters, and unique without regard to
case. Reject duplicate names with a clear message. Deleting an author with
linked books is blocked and explains that those books must first be reassigned
or deleted.

For a book form, show existing authors as an arrow-selectable list and include
an Add author choice. Adding an author opens a short name form, saves the author,
then returns to the pending book form with the new author selected. Escape
cancels author creation and returns to the book form. Keep this flow inside the
book workflow so the user does not lose entered book details.

## Book workflows

Keep the current add, view, search, update, and delete actions. Add author
selection to create and update. Before saving, preview title, author, optional
ISBN, and price. Preserve the existing ISBN-10/13 checksum validation and
uniqueness check; store a blank ISBN as SQL `NULL`. Parse prices with
`Decimal`, reject negative values and more than two decimal places, and store
them in `DECIMAL(10, 2)`.

Search with parameterized `LIKE` conditions on title and ISBN, and a join to
author name. Show the author name in every book table. Add an author-grouped
view that returns one table with an author column and the books under each
author (or a joined list of titles per author); keep keyboard menu navigation
for choosing this view. Order authors and titles alphabetically.

## Navigation and errors

The main menu opens Book Management, Author Management, or Exit. Both managers
have a Back action. Use arrow keys and Enter for selection; bind Escape to
return `None` from prompts so forms can cancel safely. Keep the existing Rich
feedback and preview/confirm patterns. Catch duplicate-key and foreign-key
errors at the workflow boundary and show a short explanation; always close
cursors and commit successful writes.

## Database startup and migration

Connect using `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, and `MYSQL_PASSWORD`.
Create the database and tables when they do not exist. Since the current app
creates tables directly at startup, add a small versioned schema check or
idempotent migration steps before changing the existing `books` table. Migrate
old records in this order: create authors, insert the placeholder author if
needed, add nullable `author_id`, backfill existing books, then make
`author_id` required and add its foreign key. A fresh database may create the
final schema directly.

## Verification

Compile the Python app and validate the Compose file. Exercise both menus against
MySQL. Verify author create/list/update/delete, duplicate-name rejection,
referential protection, adding a book with an existing author, creating an
author from the book form without losing entered details, book update and
search by author, and author-grouped display. Verify blank and supplied ISBNs,
Escape cancellation, data persistence, and migration of an existing book-only
database. Keep disposable test records out of the final database.

## Deliberately deferred

Do not implement family summaries, potential books, genres, tag search,
per-person reading history, or reading dates in this phase. The current reading
catalogue contains books the household has read; each entry does not need a
separate read/unread state yet.
