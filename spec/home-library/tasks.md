# Home Library Implementation Tasks

## 1. Repository and environment

- [x] Initialize a clean phase-one Git repository without committing prototype
  files.
- [x] Add the `uv` project, dependencies, and lockfile.
- [x] Add Docker Compose and a persistent MySQL service.
- [x] Add a containerized application service.

## 2. MySQL book storage

- [x] Connect to MySQL using environment-based settings and local defaults.
- [x] Create the `home_library` database and `books` table when absent.
- [x] Store book title, optional unique ISBN, and exact decimal price.
- [x] Upgrade existing book tables to allow omitted ISBN values.
- [x] Implement book creation, retrieval, update, and deletion with SQL.

## 3. Terminal interface

- [x] Add Rich headings, status messages, and aligned book tables.
- [x] Add arrow-key menus with Enter selection and Escape navigation.
- [x] Add book form validation and a save/edit/cancel preview.
- [x] Make ISBN optional while validating it when provided.
- [x] Add title/ISBN search and selection for update and delete.
- [x] Require confirmation before deleting a book.

## 4. Verification

- [x] Compile the Python program successfully.
- [x] Start the MySQL Compose service and run the application interactively.
- [x] Verify add, list, search, update, and delete against MySQL.
- [x] Verify a blank ISBN saves as `NULL` and displays as `—`.
- [x] Verify Escape cancels a form and returns to the menu.
- [x] Verify the collection is empty after the CRUD walkthrough.
- [x] Run final Compose configuration and Python compilation checks after the
  Escape binding fix and documentation changes.
