# Home Library Implementation Tasks

## 1. Book catalogue foundation

- [x] Set up the `uv` project and lockfile.
- [x] Add Docker Compose with persistent MySQL storage.
- [x] Build Rich terminal menus with arrow-key selection and Escape navigation.
- [x] Implement book add, view, search, update, and delete workflows.
- [x] Validate title, optional ISBN, and non-negative decimal price.
- [x] Separate domain, use cases, and persistence layers for books.
- [x] Add Unit of Work transaction handling.
- [x] Add unit, CLI, and opt-in MySQL integration tests for the book phase.

## 2. Author domain and persistence

- [x] Add `Author` and `AuthorDraft` domain models.
- [x] Validate required author name and birth date; reject numeric names,
  names without a letter, names shorter than two characters, future dates,
  and invalid dates.
- [x] Add `authors` table with a case-insensitive unique name constraint and a
  required `birth_date`.
- [x] Add required `books.author_id` foreign key with delete restriction.
- [x] Create the current required-author schema for a fresh database without
  modifying earlier database schemas.
- [x] Add author persistence operations, including search and computed book
  counts.

## 3. Author and book use cases

- [x] Implement author create, list, search, find, and update use cases.
- [x] Reject duplicate author names regardless of letter case, including
  conflicts detected by MySQL.
- [x] Require an author when creating or updating a book.
- [x] Return author-linked book details and grouped book results, including
  authors with zero books.
- [x] Keep all writes within caller-owned Unit of Work transactions.

## 4. Rich terminal workflows

- [x] Add separate Book Management and Author Management main-menu entries.
- [x] Add author add, view, search, and edit workflows; provide no delete
  action.
- [x] Show each author's derived book count and birth date.
- [x] Add searchable author selection to book create and update forms.
- [x] Support inline author creation and return to the pending book form with
  entered values intact and the new author selected.
- [x] Return to the pending book form when inline author creation is canceled.
- [x] Add author-grouped navigation with one row per author and keyboard
  expand/collapse behavior.
- [x] Preserve book preview, validation, search, and deletion confirmation
  behavior.

## 5. Verification

- [x] Test author domain validation and case-insensitive duplicate handling.
- [x] Test author CRUD use cases, derived counts, required book-author links,
  and error cases.
- [x] Test MySQL foreign keys, counts, grouped results, and one-time prototype
  data cleanup using a disposable database.
- [x] Test author menu routes, searchable author picker, inline create/cancel,
  retained book form values, and grouped-view keyboard navigation.
- [x] Verify existing book fields and operations still work with required
  authors.
- [x] Compile the application and validate Docker Compose configuration.

## 6. Later phases

- [ ] Add short family-written book summaries.
- [ ] Add a separate potential-books list.
- [ ] Add genres and genre-grouped views.
- [ ] Add searchable tags.
- [ ] Consider reading dates and per-person reading histories.
