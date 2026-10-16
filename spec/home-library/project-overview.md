# Home Library: Book Management System

## Project overview

Home Library is a command-line program for recording books owned at home. It
replaces handwritten lists with a searchable MySQL catalogue. The first version
records each book's title, optional ISBN, and price, and lets the user add,
view, search, update, or delete records.

The project is written in Python and uses SQL through MySQL Connector/Python.
The database runs in a Docker container configured with Docker Compose, while
`uv` installs and locks the Python dependencies. Rich gives the terminal output
clear headings, feedback, and aligned tables. Questionary provides keyboard
menus, with arrow keys to move, Enter to choose, and Escape to go back or cancel.

## Design intent and objectives

The design goal is to make a useful program that is easy to explain and
demonstrate. A user can understand the menu, enter a book in a short form, and
read saved details in a table. The terminal keeps the project small while
showing how Python works with a relational database.

The system aims to:

- Keep a persistent record of books owned at home.
- Reduce the effort involved in checking or correcting a handwritten list.
- Find books by a full or partial title or ISBN.
- Demonstrate Python-to-SQL connectivity, validation, and basic record
  management.
- Keep the program navigable with a consistent menu and a clear way back.

This is a personal catalogue for one user. It records books and prices, not
shop sales, library circulation, or financial transactions.

## User experience

The main menu opens Book Management or exits. Book Management offers Add, View,
Search, Update, Delete, and Back. Actions show a result and pause before the
menu returns.

For add and update, the program asks for a title, optional ISBN, and price in
rupees. It checks title length, ISBN format and checksum, duplicate ISBNs, and
non-negative prices with up to two decimal places. A preview lets the user save,
edit, or cancel. Blank ISBNs display as a dash. Deletion shows the record and
requires confirmation.

Search accepts part of a title or ISBN; a blank search shows all records. The
same aligned table displays search results and the full catalogue. Escape goes
back or cancels a form without closing the program.

<div style="page-break-after: always"></div>

## System design and data management

The application is a single Python program. Its interface collects choices and
input, validation protects the data, and SQL statements read or change the
records in MySQL. The database connection is configured through environment
variables, with defaults that match the included local Docker Compose setup.
On startup, the program creates the database and table if they are missing.
Docker Compose keeps MySQL's data in a named volume so records remain after a
container restart.

The database has one `books` table with four fields:

- `id`: generated integer primary key used to select a record.
- `title`: required book title, up to 200 characters.
- `isbn`: optional ISBN-10 or ISBN-13, unique when supplied.
- `price`: required non-negative price stored as `DECIMAL(10, 2)`.

The program uses parameterized SQL for user-provided values. ISBN validation
checks the ISBN-10 or ISBN-13 checksum, and the database's unique constraint
provides a second safeguard against duplicate ISBNs. Empty ISBN input is saved
as SQL `NULL`, which permits several books without ISBNs. Prices use Python's
`Decimal` type and MySQL's fixed-decimal type so values are not stored as
approximate binary floating-point numbers.

## Scope, security, and future development

This phase does not include author records, multiple copies, lending, borrowers,
categories, shelf locations, accounts, or a graphical interface. The database
uses the local credentials supplied for the school-project Compose setup; it is
intended for a trusted local demonstration and is not configured as a public
multi-user service. Users should keep the database container and its credentials
on their own computer.

The design leaves room to add features later without making the first version
hard to understand. A next phase could add author records and link each book to
one author, then provide an author-grouped view. Other possible extensions
include categories, locations, multiple copies, import/export, or a graphical
interface. Such changes should be planned separately so the basic catalogue
continues to have a clear data model and straightforward menus.

## Conclusion

Home Library turns a familiar task—keeping track of books at home—into a
tangible Python and SQL project. It combines a simple keyboard-driven interface
with persistent MySQL storage and validation that protects the catalogue from
common input mistakes. Its limited first-phase scope keeps the program easy to
present while providing a sound starting point for future improvements.
