# Home Library Reading Tracker Specification

## Goal

Help a household keep a simple shared record of the books its members have
read. The catalogue is the family's reading list: adding a book means it has
been read. The first release keeps this record small and easy to use, while
leaving room for family notes and discovery features later.

## Current MVP

The MVP manages books and their authors in a Rich terminal interface. A book
has a title, one author, an optional ISBN, and a price in Indian rupees. An
author has a name and may be linked to multiple books. Each book has exactly
one author in this version.

Users can add, view, search, update, and delete books; add, view, update, and
delete authors; find books by title, ISBN, or author; and view books grouped by
author. The interface uses arrow-key menus, Enter to select, and Escape to go
back or cancel. Forms validate input and show a preview before saving. Deleting
an author who still has books requires those books to be reassigned or removed
first.

ISBN is optional. When supplied, it must be a valid ISBN-10 or ISBN-13 and
unique within the catalogue. Spaces and hyphens are ignored. Price is
non-negative and has at most two decimal places. A blank ISBN is stored as
`NULL` and displayed as a dash.

## Future scope

These features are intentionally excluded from the MVP and may be planned in
later phases:

- Short family-written summaries or notes for each book.
- A separate list of potential books the family wants to read.
- Genre assignment and views grouped by genre.
- Tags that can be searched and used to organize books.
- Reading dates, individual family-member profiles, and per-person reading
  histories.

## Interface and behavior

The main menu opens Book Management, Author Management, or exits. Book
Management supports add, view, search, update, delete, and author-grouped views.
Author Management supports adding, viewing, updating, and deleting authors.
Search accepts a partial title, ISBN, or author name. Rich tables show book
titles, authors, ISBNs, and prices in aligned columns.

When adding or editing a book, the user chooses an existing author or creates
one through an author form before saving the book. The flow returns to the book
form after author creation so the user can finish the original action. The
preview allows the user to save, edit, or cancel. All cancellation and back
actions return to a usable menu without closing the program.

## Data and persistence

The program stores data in a local MySQL database managed by Docker Compose. A
book references one author; an author can be referenced by many books. Records
persist across application and container restarts through a named Docker
volume. The database contains `books` and `authors` tables. The complete field
definitions, constraints, migration, and SQL behavior are documented in
`plan.md`.

## Out of scope

- User accounts, authentication, and separate household-member histories.
- Book loans, due dates, multiple physical copies, or shelf locations.
- Online book lookup, synchronization, or cloud hosting.
- A graphical or web interface.
- Summaries, potential-reading lists, genres, and tags in this release.

## Acceptance criteria

- A user can create authors and link each book to exactly one author.
- A book form can create a missing author and return to the pending book form.
- Existing book add, list, search, update, and delete workflows continue to work.
- ISBN can be omitted; supplied ISBN values are validated and unique.
- Books can be searched by title, ISBN, or author name and viewed grouped by
  author.
- An author with linked books cannot be deleted without resolving those links.
- Escape, arrow-key navigation, form previews, and confirmations work
  consistently across both menus.
- Books and authors persist in MySQL after restarting the application.
