# Home Library

Home Library is a terminal app for tracking a household's books and authors. It supports book and author management, search, and browsing books grouped by author. The interface uses arrow-key menus and Rich tables.

## Run with Docker Compose

Requirements: Docker with the Compose plugin.

From the project directory, run:

```sh
docker compose up --build
```

This starts MySQL 8.4 and the interactive app. Use the arrow keys and Enter to navigate; press Escape to go back or cancel. The app creates the database and current tables when they are missing.

Stop the services with `Ctrl+C` or `docker compose down`. The database is stored in the `mysql_data` volume and remains available when the services are stopped.

## Run the CLI on your computer

Requirements: Python 3.10 or newer, [uv](https://docs.astral.sh/uv/), and Docker Compose (for the MySQL service).

Start MySQL, install the Python dependencies, and launch the app:

```sh
docker compose up -d mysql
uv sync --locked
uv run main.py
```

The local app uses these defaults, which match the provided Compose database settings:

| Setting | Default |
| --- | --- |
| `MYSQL_HOST` | `localhost` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | `schoolproject` |
| `MYSQL_DATABASE_NAME` | `home_library` |

Set these environment variables before `uv run main.py` to connect to a different MySQL server or database. The configured MySQL user must be able to create the database and tables if they do not exist.

## Database notes

On startup, the app creates the configured database and missing current tables. It does not migrate older schemas. Use a fresh database for this version if your database was created by an earlier version of the project. Compose stores data in a named volume, so stopping the services does not erase the catalogue.

## Project layout

- `main.py` — terminal menus, prompts, and display
- `home_library/domain/` — book and author models and validation
- `home_library/use_cases/` — application operations
- `home_library/persistence/` — MySQL access, schema, and transactions
- `spec/home-library/` — project overview and design documentation
- `tests/` — unit and MySQL integration tests
