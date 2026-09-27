# Paisa — Personal Expense Tracker

A simple, multipage expense tracker built with **Python, Flask, and MySQL**. Record everyday expenses, organize them into categories, and understand your monthly spending in **Indian Rupees (INR)**.

Designed as a bachelor's capstone project with a small, understandable codebase: server-rendered pages, three database tables, and no frontend build step.

![Paisa dashboard with monthly spending totals, daily spending chart, and category breakdown](images/WhatsApp%20Image%202026-09-27%20at%2013.13.04.jpeg)

## Contents

- [Part 1 — Understand the project](#part-1--understand-the-project)
- [Screenshots and page walkthrough](#screenshots-and-page-walkthrough)
- [Part 2 — Set up on a new laptop](#part-2--set-up-on-a-new-laptop)
- [Start the app again later](#start-the-app-again-later)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [Testing](#testing)

## Part 1 — Understand the project

### What problem does it solve?

Small expenses are easy to forget. Paisa gives users one place to record them and see how spending adds up over time.

For example, a user can record a ₹150 lunch, a ₹40 bus ticket, and ₹1,250 in groceries. The application saves the entries and calculates totals automatically.

Users enter expenses manually. The application does not connect to a bank, retrieve transactions automatically, or calculate a bank balance.

### What can users do?

| Feature | What it does |
| --- | --- |
| Registration and login | Gives each user an account with their own expenses and categories |
| Dashboard | Shows selected-month spending, average expense, top category, daily chart, and recent entries |
| Add an expense | Saves a description, amount, date, category, and payment method |
| Category dropdown | Offers starter categories and an optional inline “New category” field |
| Edit and delete | Lets users correct or remove saved expenses |
| Search and filters | Finds expenses by description, category, or month |
| CSV export | Downloads the currently filtered records for Excel or another spreadsheet app |
| Categories page | Shows each category's expense count and all-time spending |
| INR formatting | Displays rupees and paise with Indian digit grouping, such as ₹1,23,456.78 |

### Technologies in simple terms

| Technology | Its job |
| --- | --- |
| Python | The programming language used for the application |
| Flask | Receives page requests, handles forms, and runs application logic |
| Jinja and HTML | Turn application data into browser pages |
| CSS | Controls the colors, layout, spacing, and responsive design |
| JavaScript | Adds a confirmation before deleting an expense |
| MySQL | Permanently stores accounts, categories, and expense records |
| Flask-SQLAlchemy | Maps Python models to database tables and queries |
| PyMySQL | Connects the Python application to MySQL |

Google Fonts are optional; local sans-serif fonts are used if they cannot load.

### How the application works

```text
Create an account / Sign in
             ↓
         Dashboard
             ↓
     Add an expense → Choose or create a category
             ↓
 Flask validates the submitted details
             ↓
       MySQL saves the expense
             ↓
 Expenses and dashboard display the saved data
```

Flask checks the signed-in user's identity before showing protected pages. Passwords are stored as hashes rather than plain text. Expense queries are scoped to the current user, and form tokens help prevent unauthorized cross-site submissions.

### Database overview

The application uses three tables:

| Table | Information stored |
| --- | --- |
| `users` | Name, email, password hash, and account creation time |
| `categories` | Category name and the user who owns it |
| `expenses` | Description, amount, spending date, payment method, user, and category |

Each user can have many categories and expenses. Each expense belongs to one user and one of that user's categories. Money is stored using `DECIMAL` to preserve rupees and paise accurately.

Read the [database guide](database/README.md) for every column, data type, key, relationship, and example query. The actual table definitions are in [tracker/models.py](tracker/models.py).

### Short interview explanation

> “Paisa is a personal expense tracker built using Python Flask and MySQL. Users can register, log in, and manage their daily expenses. The dashboard displays monthly spending and category-wise summaries in Indian Rupees. The database has separate tables for users, categories, and expenses. The application also includes form validation, password hashing, filtering, and CSV export.”

For a demonstration, register an account, add expenses in different categories, review the dashboard, edit an expense, and export a filtered CSV. Be ready to explain how a submitted form becomes a saved database record.

## Screenshots and page walkthrough

The screenshots below are stored in the project's `images/` folder. They show an existing account; a new installation starts without expense records.

### 1. Sign in

Enter the email and password you registered with. New users select **Create an account**. This application password is separate from the MySQL password.

![Paisa login page with email and password fields](images/WhatsApp%20Image%202026-09-27%20at%2013.15.00.jpeg)

### 2. Create an account

Enter your name, email, and a password of 8–128 characters. Registration signs you in and creates starter categories. The screenshot also shows the browser's required-field message when a name is missing.

![Paisa registration page showing name, email, password, and required-field validation](images/WhatsApp%20Image%202026-09-27%20at%2013.16.30.jpeg)

### 3. Review the dashboard

The dashboard pictured at the top shows **September 2026** spending. Select a month and click **View** to change the period. Total spent, average expense, top category, and charts are calculated from that month's saved entries.

An empty month shows guidance instead of invented chart data.

### 4. Manage expenses

Use **Add expense** to create an entry. Select a category and payment method from the dropdowns; expand **New category** inside the expense form if needed. Amounts must be positive with at most two decimal places, and dates cannot be in the future.

Search or filter the list, click **Edit** to change an entry, or select **Download CSV** to export matching records. Deleting an expense is available from its edit page and cannot be undone through the app.

![Paisa expenses page with search, category and month filters, saved records, edit links, and CSV download](images/WhatsApp%20Image%202026-09-27%20at%2013.12.37.jpeg)

The Expenses screenshot includes records from multiple months, so its total differs from the selected-month dashboard total. The Categories page also uses all-time totals.

## Part 2 — Set up on a new laptop

Follow these steps once for a fresh installation. Run the commands one at a time and continue only after each succeeds.

### Step 1: Install Python and MySQL Server

You need:

- **Python 3.10 or newer**.
- **MySQL Server 8.0.16 or newer**, running locally on port `3306`.
- A browser and Terminal on macOS, or PowerShell on Windows.

MySQL Workbench is optional. It is a graphical database tool, not the database server itself. The project's setup script can create the database without Workbench.

On Windows, enable **Add Python to PATH** during Python installation. Remember the MySQL administrator (`root`) password chosen during MySQL setup.

Verify Python is installed:

```bash
# macOS
python3 --version
```

```powershell
# Windows
py --version
```

### Step 2: Copy the project and open its folder

Copy or clone this project onto the new laptop. Include `app.py`, `tracker/`, `templates/`, `static/`, `database/`, `images/`, `tests/`, `requirements.txt`, and the documentation.

Do not copy `.venv`, `.env`, or `__pycache__` from another laptop. The new installation needs its own environment and credentials.

If the project is on your Desktop:

```bash
# macOS
cd ~/Desktop/Personal_Expense_Tracker
```

```powershell
# Windows PowerShell
cd "$HOME\Desktop\Personal_Expense_Tracker"
```

If you saved it elsewhere, use that folder's actual path. Run all remaining commands from the project folder.

### Step 3: Create the Python environment

A virtual environment keeps this project's Python packages together.

```bash
# macOS
python3 -m venv .venv
source .venv/bin/activate
```

```powershell
# Windows PowerShell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation, `(.venv)` should appear in your terminal prompt.

### Step 4: Install the required packages

```bash
python -m pip install -r requirements.txt
```

This installs Flask, database libraries, and the test runner. Installation requires an internet connection.

### Step 5: Make sure MySQL is running

On macOS, use the server controls provided by your MySQL installation. If you installed the `mysql@8.4` Homebrew package, use:

```bash
brew services start mysql@8.4
```

On Windows, open **Services**, find your MySQL service, and choose **Start** if it is stopped.

### Step 6: Run the database setup script

```bash
python database/setup.py
```

When prompted:

```text
MySQL root password (Enter if none was set):
```

Enter the root password chosen during MySQL installation. Password characters will not appear while typing. Press Enter without typing only if your local MySQL installation has no root password.

The script automatically:

1. Creates the `expense_tracker` database.
2. Creates the `expense_app` database user if it does not exist.
3. Generates a password for a new application database user.
4. Verifies that the application can connect.
5. Saves settings privately in `.env`.
6. Generates the application's session secret if it is missing.

You do not need to edit an SQL file, copy `.env.example`, or manually generate a password. The setup file is [database/setup.py](database/setup.py).

Existing database-user passwords are not changed. If `expense_app` already exists, `.env` must contain its correct password. The script is intended for the default local server and stops if `.env` contains a custom host, port, database name, or username.

Keep `.env` private. It is ignored by Git.

### Step 7: Create the tables

```bash
flask --app app init-db
```

Expected message:

```text
Database tables are ready. Open the app to create your account.
```

This creates `users`, `categories`, and `expenses` using the Python models. It creates missing tables; it does not migrate the structure of existing tables.

### Step 8: Start Flask

```bash
flask --app app run --port 5001
```

Open **http://127.0.0.1:5001** in your browser.

`127.0.0.1` means your own laptop. The application is running locally, not published on the internet. Keep the terminal open while using it.

### Step 9: Register and try the application

1. Click **Create an account**.
2. Enter your name, email, and a new application password.
3. Add an expense such as “Lunch”, ₹150, today's date, Food & Dining, and UPI.
4. Confirm that it appears on the Expenses page.
5. Open the Dashboard and check the selected month's total.

There are no built-in application login credentials. Email verification is not implemented.

### Which password is which?

| Password | Purpose |
| --- | --- |
| MySQL root password | Used by the setup script to prepare the database |
| Application database password | Generated for `expense_app`, stored in `.env`, and used by Flask |
| Paisa login password | Chosen during registration and entered in the browser |

### Moving existing records

Copying the project folder does not transfer accounts or expenses. For those, export the old laptop's `expense_tracker` database, including structure and data, and restore that backup into a fresh database on the new laptop. A CSV export is not a complete database backup.

Separate local installations do not synchronize automatically.

## Start the app again later

First make sure MySQL is running. Then open the project folder and activate the environment.

**macOS:**

```bash
cd ~/Desktop/Personal_Expense_Tracker
source .venv/bin/activate
flask --app app run --port 5001
```

**Windows PowerShell:**

```powershell
cd "$HOME\Desktop\Personal_Expense_Tracker"
.\.venv\Scripts\Activate.ps1
flask --app app run --port 5001
```

Open **http://127.0.0.1:5001**. Do not repeat installation, `setup.py`, or `init-db` for normal use.

Press **Control + C** in Terminal to stop Flask. Saved records remain in MySQL. Closing the browser alone does not stop the server.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `flask: command not found` | Activate `.venv` and ensure dependencies are installed |
| MySQL connection refused | Start MySQL and check that it is listening on local port 3306 |
| Access denied during setup | Check the root password; if `expense_app` already exists, check its password in `.env` |
| Missing `SECRET_KEY` | On a fresh installation, complete `python database/setup.py` successfully |
| Unknown database | Complete the database setup script |
| Table does not exist | Run `flask --app app init-db` |
| Browser cannot connect | Keep Flask running and use the same port shown in Terminal |
| Port 5001 is occupied | Check whether the app is already running; otherwise use `--port 5002` and open that port |
| Dashboard is empty | Add an expense and select the month containing its date |

If Windows blocks environment activation, use its Python executable directly without changing your system's execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe database/setup.py
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app run --port 5001
```

## Project structure

```text
Personal_Expense_Tracker/
├── app.py                  Flask entry point
├── tracker/
│   ├── __init__.py         App configuration, CSRF, and INR formatting
│   ├── models.py           Database table definitions
│   └── routes.py           Login, forms, dashboard, filters, and export
├── templates/              HTML page templates
├── static/
│   ├── style.css           Responsive interface styling
│   └── app.js              Delete confirmation
├── database/
│   ├── setup.py            Local database and .env setup
│   └── README.md           Column definitions and relationship guide
├── images/                 Screenshots used in this README
├── tests/
│   └── test_app.py         Automated application checks
├── .env.example            Example configuration for reference
├── .gitignore              Excludes secrets and generated files
├── requirements.txt        Python dependencies
└── README.md               Project explanation and setup instructions
```

`.env` and `.venv/` are created locally. Earlier files such as `expense_tracker.py`, `modules/`, and `expenses.json` are legacy reference only and are not used by the Flask application. JSON records are not automatically imported.

## Testing

With the virtual environment active:

```bash
python -m pytest -q
```

The tests cover authentication, protected pages, expense creation/editing/deletion, totals, filtering, CSV export, custom categories, invalid inputs, form tokens, and account isolation. They use a disposable SQLite database with foreign keys enabled and do not touch personal MySQL data.

For a manual MySQL check, register an account, add and edit an expense, confirm the dashboard total, export a CSV, restart Flask, and confirm the saved record is still present. Use a second account to verify that its expense list is separate.

## Scope and future improvements

This is a local educational project. Possible extensions include monthly budgets, recurring expenses, password recovery, email verification, and pagination for larger datasets.

The current expense list loads all matching records. Public hosting would also require a production server, HTTPS, login abuse controls, and an appropriate deployment configuration. Database structure changes require migrations rather than rerunning `init-db`.
