# Home Library Author Management Specification

## Goal

Extend the Home Library catalogue so every book is linked to one author. The
author can be selected from the existing catalogue or created while a book is
being added or edited. Keep the app local, single-user, and simple to operate
from its Rich terminal interface.

## MVP behavior

The application has separate Book Management and Author Management menus.
Books can be added, viewed, searched, updated, and deleted. Authors can be
added, viewed, searched, and edited. Authors cannot be deleted. Every book
must have exactly one author, and an author may have zero or more books.

A book keeps its existing title, optional ISBN, and price fields, and gains a
required author. ISBN remains optional and unique when supplied. Search supports
partial, case-insensitive matches for book title, ISBN, and author name.

## Author information and rules

An author has a required name and required date of birth. Names are trimmed,
must contain at least two characters, include a letter, and cannot contain
numbers. Names must be unique without regard to capitalization. Different
authors with the same name are not allowed. Date of birth must be a valid
calendar date and cannot be in the future; the terminal form uses `YYYY-MM-DD`.

Each author view displays the number of linked books. This count is calculated
from the books table, starts at zero, and changes as books are added or removed.
The user does not enter or edit the count.

## Book and author workflows

When adding or editing a book, the user must select an author using a
searchable, arrow-key list. If the desired author is not present, the user can
create one from that flow. The app validates and saves the author, selects it
for the pending book, and returns to the unfinished book form with entered
book details intact. If author creation is canceled with Escape, the app
returns to that unfinished book form so the user can choose another author or
cancel the book operation.

Author Management supports adding, viewing, searching, and editing authors.
Author selection and edit selection are searchable and distinguish results
using their birth dates. Editing an author changes the existing author record,
so every linked book displays the updated name and date. No author deletion
action is provided.

## Grouped books view

The Book Management menu includes a view grouped by author. It shows one
selectable row per author, including authors with no books. Enter or the
right-arrow expands an author row to show its book titles. Enter or the
left-arrow collapses the row. Escape returns to the previous menu. Because
every book has an author, there is no unassigned-books group. Authors with no
books show an empty-state message when expanded.

## Database setup

The application supports a fresh database using the current schema. It does
not migrate or modify databases created by earlier project versions. Before
using this version with an existing database, the user must create a fresh
database themselves. The application must not automatically delete or rewrite
existing tables or records.

## Interface behavior

Use Rich tables and arrow-key menus with Enter to select and Escape to go back
or cancel. Forms validate values, preserve entered values when returning from
inline author creation, and preview changes before saving. Confirm deletion of
books. Show clear validation, duplicate-name, not-found, and database error
messages. Pause after completed actions before returning to the menu.

## Future scope

Keep these out of this author phase: family-written summaries, a potential
books list, genres, tags, family-member profiles, and per-person reading
histories.

## Acceptance criteria

- Every book in the final catalogue has exactly one existing author.
- An author can be added with a valid unique name and a required past or
  present birth date.
- Duplicate names are rejected even when capitalization differs.
- The displayed book count is derived from linked books and updates after
  adding or deleting a book.
- Author search is partial and case-insensitive.
- A user can create an author from a pending book form without losing the
  book's entered fields; Escape during author creation returns to that form.
- Book author selection and update are searchable and use arrow navigation.
- Author management supports add, view, search, and edit, with no delete
  action.
- Editing an author updates the details displayed for every linked book.
- The grouped view has one row per author, supports keyboard expand/collapse,
  and includes authors with zero books.
- Fresh database setup creates the current schema with the required author
  relationship and does not alter existing tables.
- Existing book title, optional ISBN, price, search, and CRUD behavior continue
  to work.
