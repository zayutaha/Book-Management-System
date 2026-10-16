# Home Library Implementation Tasks

## 1. Existing book catalogue

- [x] Set up the `uv` project and lockfile.
- [x] Add Docker Compose with persistent MySQL storage.
- [x] Build Rich terminal menus with arrow-key selection and Escape navigation.
- [x] Implement book add, view, search, update, and delete workflows.
- [x] Validate title, optional ISBN, and non-negative decimal price.
- [x] Verify book CRUD against the MySQL container.

## 2. Layered architecture for books

- [x] Move book entities and input rules into `home_library/domain`.
- [x] Move book workflows into `home_library/use_cases`.
- [x] Move MySQL connection, schema setup, SQL, and row mapping into
  `home_library/persistence`.
- [x] Keep the terminal adapter free of SQL and cursor handling.
- [x] Add a Unit of Work for caller-controlled MySQL transactions.
- [x] Verify domain validation, MySQL-backed use-case CRUD, and the terminal
  add/delete flow.

## 3. Author data and relationship

- [ ] Add an authors table with a unique required name.
- [ ] Link every book to one author with a foreign key.
- [ ] Migrate existing books to an explicit placeholder author without losing
  records.
- [ ] Prevent deleting authors that still have linked books.

## 4. Author interface and book integration

- [ ] Add Author Management actions to the main menu.
- [ ] Implement author add, list, update, and delete workflows.
- [ ] Add author selection to book create and update forms.
- [ ] Allow creating a missing author from the book form and return to the
  pending book form with its entered details preserved.
- [ ] Show author names in book tables and search results.
- [ ] Add an author-grouped books view.

## 5. Verification

- [ ] Compile the app and validate the Compose configuration.
- [ ] Verify author CRUD and duplicate-name handling.
- [ ] Verify author deletion protection and the existing-data migration.
- [ ] Verify book creation with an existing and newly created author.
- [ ] Verify book search by title, ISBN, and author, plus author grouping.
- [ ] Recheck ISBN optionality, Escape behavior, and persistence.

## 6. Later phases

- [ ] Add short family-written book summaries.
- [ ] Add a separate potential-books list.
- [ ] Add genres and genre-grouped views.
- [ ] Add searchable tags.
- [ ] Consider per-person reading histories and reading dates.
