# Home Library Technical Plan

## Architecture

Keep the first phase as one small Python program. `main.py` owns terminal
navigation, input validation, MySQL access, and book workflows. Rich renders
panels, tables, and messages; Questionary and prompt-toolkit provide keyboard
menus and Escape handling.

```text
Rich / Questionary terminal interface -> book workflows -> MySQL
```

## Environment

Use `uv` for Python dependency and lockfile management. Use Docker Compose to
run MySQL 8.4 with a persistent named volume. Keep the command-line app usable
from the host and provide a containerized app service for a one-command run.
Keep the earlier prototype outside the phase-one Git history.

## Database setup

On connection, create the `home_library` database and `books` table if needed.
Use a generated integer primary key, a required title, a unique ISBN, and an
exact `DECIMAL(10, 2)` price with a non-negative database constraint. Commit
each create, update, or delete operation explicitly.

## Book workflows

For add and update, collect and validate the title, ISBN, and price before
showing a Rich preview. Let the user save, edit the details, or cancel. Validate
ISBN-10 and ISBN-13 checksums and query the database for duplicate ISBN values;
exclude the selected row during an update. Search title and ISBN with a
parameterized `LIKE` query. Display results in title order. Require confirmation
before deleting a selected record.

## Navigation

The main menu opens book management or exits. The book menu provides add, view,
search, update, delete, and back actions. Use arrow-key selection and Enter for
menus, and bind Escape to return `None` so workflows can cancel or go back
without terminating the program. Pause after a workflow result before drawing
the next menu.

## Validation

Check Python compilation and Compose configuration. Exercise the interface
against the running MySQL container: add and list a record, search it, update
it, delete it, confirm an empty list, cancel a form with Escape, and exit. Keep
the database test collection empty after the walkthrough.

## Future work

Add authors and author-based grouping in a later phase. Any such change should
define how author records are created and linked before expanding the schema or
menus. Loans, multiple users, and a graphical interface remain separate scope
decisions.
