# Home Library Author Feature Implementation Plan

This document describes implementation details for the product behavior in
[`spec.md`](spec.md). Keep the implementation in the existing
`domain` / `use_cases` / `persistence` layers and the Rich CLI adapter.

## Runtime and architecture

Continue using Python managed by `uv`, Rich and Questionary for the terminal
interface, MySQL for persistence, and Docker Compose for the local database.
Keep `main.py` focused on prompts, navigation, rendering, and calling use
cases. Keep SQL and connector code out of the CLI and domain.

```text
main.py -> use_cases -> persistence -> MySQL
               |             |
               +-> domain <-+
```

Suggested modules:

```text
home_library/
  domain/
    author.py
    book.py
    errors.py
  use_cases/
    authors.py
    books.py
  persistence/
    authors.py
    books.py
    schema.py
    unit_of_work.py
```

## Domain

Add an `Author` read model with `id`, `name`, `birth_date`, and computed
`book_count`, plus an `AuthorDraft` for validated create/update input. Represent
birth dates as `datetime.date`. Keep the book count as query output; do not
store or accept it as editable data.

Add validation for trimmed author names, length from 2 through 200 characters,
at least one letter, and no numeric characters. Allow ordinary Unicode
letters, spaces, and common name punctuation. Reject names that are blank or
consist of fewer than two characters after trimming. Validate that birth dates
are real dates and are not later than the current date.

Extend the `Book`/`BookDraft` domain representation with the required author
identifier and author display name where needed by list/search/grouped
queries. Keep current title, optional ISBN checksum/uniqueness, and Decimal
price rules. A book draft without an author ID is invalid.

## Use cases

Add author operations for create, list, search, find, and update. Author
creation and rename must enforce case-insensitive name uniqueness; translate a
database unique-key race to a clear `DuplicateAuthorName` application error.
Search trims input and supports partial case-insensitive name matches.

Update book create and update workflows to require a valid author ID. Add
operations to search authors for book selection, return book counts with
author records, and list books grouped by author. Grouped results include
authors with zero books and return their books in title order. Keep all write
operations inside the caller-provided Unit of Work.

There is no author delete use case. The persistence foreign key also uses
`ON DELETE RESTRICT` as a data-integrity backstop.

## Persistence

Create an `authors` table and update `books`:

| Table | Field | Type and constraints |
| --- | --- | --- |
| `authors` | `id` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `authors` | `name` | `VARCHAR(200) NOT NULL`, unique case-insensitively |
| `authors` | `birth_date` | `DATE NOT NULL` |
| `books` | `id` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `books` | `title` | `VARCHAR(200) NOT NULL` |
| `books` | `author_id` | `INT NOT NULL`, foreign key to `authors.id` |
| `books` | `isbn` | `VARCHAR(13) NULL UNIQUE` |
| `books` | `price` | `DECIMAL(10, 2) NOT NULL`, zero or greater |

Use a case-insensitive database collation or a normalized unique key for author
names while preserving the entered display casing. Queries for author counts
must use `COUNT(books.id)` with a left join so authors with zero books remain
visible. Grouped-book queries must use parameterized SQL and return structured
domain data, not connector rows or formatted output.

## Migration

Use a versioned migration so the book-only schema can be distinguished from
the new schema. The user explicitly chose to discard all existing prototype
book rows because they do not have required authors. During migration:

1. Create the authors table and its case-insensitive unique name constraint.
2. Delete existing rows from the prototype `books` table.
3. Add the required `author_id` column and its foreign key.
4. Record the schema version so the deletion cannot run again on later starts.

Do not create an `Unknown` author or leave a nullable `author_id`. The migration
must preserve the database and new schema while intentionally clearing only
the old prototype book records. Show a clear notice before deleting those
records. On a fresh database, create the final schema directly without a
cleanup step.

## CLI flows

Add Author Management to the main menu with add, view, search, and edit. Do not
show a delete action. Author tables show name, birth date, and derived book
count. Add and edit forms preview values before saving.

Build a reusable searchable author picker for create and edit book workflows.
Picker rows should include both name and birth date. When no result matches,
offer an inline create-author action. After successful author creation, return
to the pending book form with all book fields preserved and the new author
selected. If author creation is canceled, return to the pending book form and
keep entered values.

For author grouping, render one keyboard-selectable row per author. Enter or
right-arrow expands the selected row to show that author's book titles; Enter
or left-arrow collapses it; Escape returns to the previous menu. Include
authors with no books and show a short empty state when expanded. Keep search
and selection accessible by keyboard.

## Verification

Add domain tests for author name and date validation; use-case tests for
duplicate-name handling, book counts, author assignment, and update behavior;
persistence tests for case-insensitive uniqueness, foreign keys, counts,
grouped results, and the one-time migration; CLI tests for author menu routing,
searchable selection, inline author creation/cancellation, form state
preservation, validation, and grouped-view keyboard behavior.

Run unit tests without a database and opt-in MySQL integration tests against a
disposable schema. Verify that the prototype migration removes old book rows
once, preserves the new schema on a subsequent start, and does not touch the
normal user database during tests.

## Out of scope

Do not add author deletion, author biographies, summaries, potential-book
lists, genres, tags, reading dates, family profiles, per-person histories,
accounts, or a graphical interface in this phase.
