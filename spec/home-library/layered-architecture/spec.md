# Home Library Layered Architecture Specification

## Goal

Separate Home Library's application logic into three clear parts: `domain`,
`use_cases`, and `persistence`. Keep the existing Rich terminal UI as a thin
entry-point adapter. The structure should make each part easy to explain and
change without scattering SQL, validation, and prompts through one file.

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
    errors.py
  persistence/
    __init__.py
    database.py
    schema.py
    authors.py
    books.py
    unit_of_work.py
```

`main.py` owns Rich rendering, Questionary prompts, menu navigation, and
translation of use-case results into messages. It may call exported use cases
and display returned domain objects. It must not issue SQL, manage cursors, or
perform business validation itself.

## Domain

Define `Author` and `Book` as simple Python domain objects. A book contains its
ID, title, author, optional ISBN, and price. An author contains its ID and name.
Represent prices with `Decimal`; represent an omitted ISBN as `None`.

Place rules that do not require user interaction or a database here: trimmed
non-empty names and titles, maximum text lengths, ISBN normalization and
checksum validation, non-negative two-decimal prices, and the one-author-per-
book relationship. Domain code must not import Rich, Questionary,
`mysql.connector`, environment settings, or persistence modules.

## Use cases

Expose plain functions for the application actions, grouped by books and
authors. Use cases receive validated command data, call domain rules, invoke
persistence operations, and return domain objects or a clear result. They do
not prompt, print, render tables, read environment variables, or contain SQL.

The supported operations are:

- Create, list, search, update, and delete books.
- Create, list, update, and delete authors.
- List books grouped by author.
- Create an author and its book in one save operation when the user adds a
  missing author from a book form.

Cancellation is handled by the interface before a write use case is called.
The create-book workflow must not leave an orphan author when the user cancels
before saving the book. Duplicate authors and deletion of an author with linked
books return clear use-case errors for the interface to display.

## Persistence

The persistence package owns MySQL connection configuration, database/table
creation or migrations, transaction handling, parameterized SQL, and mapping
database rows into domain objects. Keep SQL row representations private to
their persistence modules. Return `Author` and `Book` objects rather than raw
tuples or connector rows.

Provide focused operations for author and book reads/writes. Search and
author-grouped queries may use SQL joins, but persistence returns structured
domain data; it does not format Rich tables. Preserve existing records when
migrating the book-only schema to authors and `author_id`.

Use a small Unit of Work or transaction context for writes that must succeed or
fail together, especially saving a new author and its book. The CLI adapter
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
Use cases translate expected conflicts, missing records, and blocked deletes
into clear application errors. The interface chooses the wording and style of
the displayed message.

Each write use case accepts the unit of work from its caller. Book and author
creation from a single form is atomic. Updating a book, deleting a book, or
adding an author is committed as one operation. A failed validation or
persistence write must not partially change the catalogue.

## Acceptance criteria

- The UI contains no SQL statements, MySQL connector calls, or cursor handling.
- Domain modules have no imports from the interface or persistence layers.
- Use cases contain workflow coordination and call persistence functions rather
  than embedding SQL.
- Persistence modules own MySQL setup, migrations, SQL, and row mapping.
- Callers receive domain objects instead of raw database tuples.
- Creating a missing author with a book is atomic and cancellation writes
  nothing.
- Existing book and author behavior remains available through the terminal
  interface after the refactor.
- The package structure remains small and explainable, without generic
  repository or dependency-injection machinery.

## Out of scope

- Changing the Rich interface or product feature set.
- Implementing future summaries, potential books, genres, tags, or family
  member histories.
- Replacing MySQL, Docker Compose, or `uv`.
- Introducing a web/API layer, ORM, generic repository framework, or plugin
  architecture.
