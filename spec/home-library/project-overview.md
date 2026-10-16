# Home Library: Family Reading Tracker

## Project purpose

Home Library helps a household keep a shared record of books its members have
read. A family may remember a story but forget its title or author; this
catalogue gives them one place to check what has already been read. The project
turns that familiar need into a practical Python application that can be used
and demonstrated at school.

The catalogue is intentionally small in its first release. A record represents
a book the household has read. The current MVP lets users manage books and
authors, find a title later, and browse books grouped by author. It is designed
as a shared household list rather than separate accounts or a social reading
network.

## Design intent

The program should be easy to learn and easy to explain. Its terminal interface
uses clear menus, short forms, readable tables, and direct success or error
messages. Users move through choices with the arrow keys, select with Enter,
and use Escape to go back or cancel. Before a book is saved or removed, the
program shows its details and gives the user a chance to confirm or revise.

The design favors a few dependable actions over a large set of screens. The
same book information appears consistently in lists, search results, previews,
and author views. Input checks help prevent blank titles, invalid or duplicate
ISBNs, and invalid prices. The project remains approachable for a student
presentation while solving a real record-keeping problem.

## Current MVP

The main menu has Book Management and Author Management. Users can add, view,
search, update, and delete book records; add, view, search, and edit authors;
and view books grouped by author. A book has a title, exactly one required
author, an optional ISBN, and a price in Indian rupees. Each author has a
unique name, date of birth, and a displayed count of linked books. The count is
calculated by the app rather than entered by the user.

If an author is missing while adding or editing a book, the user can create
that author inline and return to the unfinished book form with its details
preserved. Author selection and search use arrow-key navigation. Search accepts
a partial, case-insensitive title, ISBN, or author name. The grouped view shows
one row per author and lets users expand a row to see its books. Authors cannot
be deleted. The application creates the current schema for a fresh database
and does not migrate or modify databases from earlier project versions. The
MVP is a local shared catalogue; it does not identify which family member read
each title or record when it was read.

<div style="page-break-after: always"></div>

## Future development

The following ideas are part of the longer-term vision and are deliberately
outside the current MVP:

- **Family summaries:** let family members write short summaries or notes about
  a book, so they can remember what they thought of it.
- **Potential books:** keep a separate list of books the family may want to
  read, distinct from the record of books already read.
- **Genres:** assign genres and browse or group books by genre.
- **Tags:** add flexible tags and search for books using them.
- **Reading history:** record who read each book and when, if the family needs
  individual histories later.

These features should be added in later phases after the book and author flows
are dependable. Keeping them out of the MVP makes it possible to focus on the
main task: recording and finding books the family has read. The full future
scope is listed in `spec.md`.

## Scope and value

Home Library replaces handwritten lists and scattered notes with a persistent
digital record. It can save time when a family wants to remember whether a book
has already been read, find an author, or browse their reading history by
author. It also demonstrates how a Python interface can validate information
and manage related records in a database.

The current release does not handle lending, multiple physical copies, book
sales, online lookup, accounts, or cloud access. It is intended for use on a
trusted local computer. Those limits keep the project useful without making it
hard to build, operate, or describe.

## Implementation documentation

This overview explains the project's purpose, user experience, and product
scope. The separate `plan.md` records the technical design, database schema,
interface workflows, and verification approach. `tasks.md`
tracks implementation work and future phases.
