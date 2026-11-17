# Service Information Management System

A beginner-friendly CRUD web application built with Python Flask, MySQL, HTML, CSS and JavaScript. It follows the service-listing screen shown in the assignment screenshots.

## Features
- Create, read, update and delete service records
- List screen with case ID, requested date, customer, product, region, status and TAT
- Filters: date raised, location, region, status, reopened cases and TAT status
- Search visible records
- Export CSV
- Print table
- Reopen closed cases
- Automatic TAT calculation using request time, closed time and target days

## Requirements
- Python 3.10+
- MySQL Server 8+
- VS Code (recommended)

## Setup (Windows)

1. Extract the ZIP and open this folder in VS Code.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Create the database and table. In MySQL Workbench or phpMyAdmin, open `schema.sql` and execute it.
6. Copy `.env.example` to a new file named `.env`. Update `DB_USER`, `DB_PASSWORD`, and other values to match your MySQL setup.
7. Start the app:

   ```bash
   python app.py
   ```

8. Open http://127.0.0.1:5000 in your browser.

## Setup (macOS / Linux)

Activate the environment with:

```bash
source venv/bin/activate
```

The remaining steps are the same.

## Notes
- The app uses a local development server. Do not deploy it publicly with `debug=True`.
- Change `FLASK_SECRET_KEY` to a long random value before deployment.
- The app expects the database table to be named exactly `serviceInfo`.
- The schema includes the columns visible in the assignment plus `closedAt`, `isReopened`, and `tatTargetDays` to support the requested TAT and reopen features.
- TAT is measured as elapsed calendar days. The sample target is 7 days; adjust each record's target as needed.
- The CSV export includes the main record fields. The list screen's date and TAT filters are applied in the browser/server list; CSV export currently applies search, location, region, status and reopen filters.
- For a real production system, add login/authorization, CSRF protection, server-side pagination, validation, secure secret management, and upload handling for issue images.

## Interview preparation
Be ready to explain:
- Flask routes and HTTP methods (GET and POST)
- SQL INSERT, SELECT, UPDATE and DELETE
- Parameterized SQL queries and SQL injection prevention
- MySQL connection, cursor and commit
- How filters are translated into SQL WHERE conditions
- TAT calculation and case reopening
- How HTML forms send data to Flask and how Flask renders templates
