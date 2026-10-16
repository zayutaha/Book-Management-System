# Home Library Layered Architecture Specification

## Goal

Keep the book catalogue and its author feature in three clear parts:
`domain`, `use_cases`, and `persistence`. Keep the Rich terminal UI as a thin
entry-point adapter. The structure should make each part easy to explain and
change without scattering SQL, validation, and prompts through one file. The
existing book code already follows these boundaries; author behavior extends
the same structure.

This specification concerns code organization and boundaries. Product behavior
remains defined by [`../spec.md`](../spec.md), and database/runtime details
remain in [`../plan.md`](../plan.md).

## Mothership pattern

Follow the small vertical-slice structure used by Mothership's account budgets:

- `domain` defines application data types without SQL dependencies.
- `use_cases` coordinates a user action and enforces its workflow rules.
- `store` (named `persistence` in this Python project) owns SQL, row mapping,
  and database access.
- A module entry point exposes the supported domain types and use cases while
  keeping storage details private.

In Mothership, these parts are `domain.rs`, `use_cases.rs`, and `store.rs` under
`crates/mothership-core/src/account_budgets/`. SQL row structs stay inside the
store, and use cases receive a `UnitOfWork` for the transaction they use. Home
Library should adapt these boundaries to Python and MySQL without copying Rust
crate or async patterns that the school project does not need.

## Target structure

```text
main.py
home_library/
  __init__.py
  domain/
    __init__.py
    author.py
    book.py
    errors.py
  use_cases/
    __init__.py
    authors.py
    books.py
  persistence/
    __init__.py
    authors.py
    database.py
    errors.py
    schema.py
    books.py
    unit_of_work.py
```

`main.py` owns Rich rendering, Questionary prompts, menu navigation, and
translation of use-case results into messages. It may call exported use cases
and display returned domain objects. It must not issue SQL, manage cursors, or
perform business validation itself.

## Domain

Define `Book`, `BookDraft`, `Author`, and `AuthorDraft` as simple Python domain
objects. A book contains its ID, title, required author ID, optional ISBN, and
price. An author contains its ID, name, birth date, and a computed book count.
Represent prices with `Decimal`, an omitted ISBN as `None`, and birth dates
with `datetime.date`.

Place rules that do not require user interaction or a database here: trimmed
non-empty titles, maximum text lengths, author names of at least two
characters with a letter and no numbers, valid non-future birth dates, ISBN
normalization and checksum validation, and non-negative two-decimal prices. Author names
must be unique case-insensitively, enforced by a use case and database
constraint. Domain code must not import Rich, Questionary, `mysql.connector`,
environment settings, or persistence modules.

## Use cases

Expose plain functions for book and author actions. Use cases receive
validated command data, call domain rules, invoke persistence operations, and
return domain objects or a clear result. They do not prompt, print, render
tables, read environment variables, or contain SQL.

The supported operations are:

- Create, list, search, update, and delete books.
- Create, list, search, find, and update authors.
- Return computed author book counts and author-grouped book records.
- Require an author for each book.

Cancellation is handled by the interface before a write use case is called.
There is no author-deletion use case.

## Persistence

The persistence package owns MySQL connection configuration, database/table
creation or migrations, transaction handling, parameterized SQL, and mapping
database rows into domain objects. Keep SQL row representations private to
their persistence modules and return `Book` or `Author` objects rather than
raw tuples or connector rows.

Provide focused operations for author and book reads and writes. Persistence
returns structured domain data; it does not format Rich tables. Keep schema
setup and the versioned migration that discards prototype book rows inside
this package.

Use a small Unit of Work or transaction context for writes. The CLI adapter
opens the unit of work, passes it to a use case, and commits only when the use
case succeeds; an error leaves the unit uncommitted and rolls it back. This
mirrors Mothership's caller-owned transaction boundary, adapted to the terminal
entry point. Avoid a generic repository framework or dependency-injection
container; the direct `use_cases -> persistence` relationship follows
Mothership's `use_cases -> store` pattern and is simpler to present.

## Dependency direction

```text
main.py -> use_cases -> persistence
               |             |
               +-> domain <-+
```

The domain depends on no other project layer. Persistence may import domain
types to construct return values. Use cases coordinate both. The interface
depends on use cases and domain types, never on persistence.

## Errors and transactions

Domain validation errors should be specific and independent of the terminal.
Persistence translates MySQL failures into a small persistence error type.
Use cases translate expected conflicts and missing records into clear
application errors. The interface chooses the wording and style of the
displayed message.

Each write use case accepts the unit of work from its caller. Creating,
updating, or deleting a book is committed as one operation. A failed validation
or persistence write must not partially change the catalogue. The MySQL
foreign key requires `books.author_id`; author names have a case-insensitive
unique constraint. Do not add author deletion.

## Acceptance criteria

- The UI contains no SQL statements, MySQL connector calls, or cursor handling.
- Domain modules have no imports from the interface or persistence layers.
- Use cases contain workflow coordination and call persistence functions rather
  than embedding SQL.
- Persistence modules own MySQL setup, migrations, SQL, and row mapping.
- Callers receive domain objects instead of raw database tuples.
- Author and book workflows stay within their domain, use-case, and
  persistence modules.
- Book records always reference an author; author book counts are computed.
- Existing book add, view, search, update, and delete behavior remains available
  through the terminal interface after the refactor.
- The package structure remains small and explainable, without generic
  repository or dependency-injection machinery.

## Out of scope

- Implementing future summaries, potential books, genres, tags, or family
  member histories.
- Changing the Rich interface or product feature set beyond the author
  workflows in the product specification.
- Replacing MySQL, Docker Compose, or `uv`.
- Introducing a web/API layer, ORM, generic repository framework, or plugin
  architecture.
