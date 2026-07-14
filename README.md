# Zenit

Personal finance management web application built with Django.  
The project centralizes account, category, and transaction management, displays dashboard indicators, generates reports, and provides AI-assisted financial analysis.

## Features

- Email authentication (login, logout, registration).
- Dashboard with total balance, monthly income/expenses, and recent transactions.
- CRUD for accounts, categories, and transactions.
- Transaction filters by month, year, type, and category.
- Transaction export to CSV and PDF.
- Reports with charts (last 12 months and expenses by category).
- User profile (phone and avatar).
- AI financial analysis for a period (`YYYY-MM`) with an income, expense, and balance snapshot.

## Technologies Used

- Python 3.14
- Django 6
- SQLite (default) with `DATABASE_URL` support via `dj-database-url`
- LangChain + `langchain-openai` (AI module)
- Pytest + pytest-django + pytest-cov
- `uv` for dependency management

## Project Structure

```text
core/           # Global configuration (settings, urls, base views)
users/          # Custom user and authentication
accounts/       # Bank accounts/wallet
categories/     # Income and expense categories
transactions/   # Transactions, filters, and exports
reports/        # Reports and charts
profiles/       # User profile
ai/             # Financial analysis with a LangChain/OpenAI agent
templates/      # HTML templates by module
```

## Running Locally

1. Install dependencies:

```bash
uv sync --dev
```

2. Configure the environment:

```bash
cp .env.example .env
```

3. Apply migrations:

```bash
uv run python manage.py migrate
```

4. (Optional) Seed initial categories:

```bash
uv run python manage.py seed_categories
```

5. Start the server:

```bash
uv run python manage.py runserver
```

Access:
- `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Environment Variables

Available template:

- `.env.example`: single base for development and production.

For local development:

```bash
cp .env.example .env
```

To prepare production:

```bash
cp .env.example .env.prod
```

In the production file (`.env.prod`), configure at least:
- `DJANGO_ENV=production`
- `DEBUG=False`
- `ALLOWED_HOSTS` with the real domain(s)
- `DATABASE_URL` with PostgreSQL

Relevant variables:

- `SECRET_KEY`
- `DJANGO_ENV`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL` (in production, use a PostgreSQL URL)
- `OPENAI_API_KEY` (required for AI analysis)
- `OPENAI_MODEL` (default: `gpt-5-mini`)

## Tests

Run all tests:

```bash
uv run pytest
```

Notes:
- The suite requires minimum **80%** coverage (`--cov-fail-under=80`).
- Example focused run:

```bash
uv run pytest ai/tests/test_agent.py
```

## AI Notes

- The `POST /ai/analyze/` endpoint requires an authenticated user.
- Analysis requires at least 3 transactions in the requested period.
- If a completed analysis already exists from the last 24 hours for the same period, the system reuses the result.
