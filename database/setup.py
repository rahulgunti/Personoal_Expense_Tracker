"""Create the local database using the same procedure used for this project.

Run once on a new laptop: python database/setup.py
MySQL must already be installed and running on the default local port (3306).
"""
from getpass import getpass
from pathlib import Path
import secrets

import pymysql
from dotenv import dotenv_values, set_key


def main():
    project = Path(__file__).resolve().parent.parent
    env = project / '.env'
    if not env.exists():
        env.touch(mode=0o600)
    values = dotenv_values(env)
    # This setup script configures only the standard local project database.
    expected = {
        'DB_HOST': '127.0.0.1', 'DB_PORT': '3306',
        'DB_NAME': 'expense_tracker', 'DB_USER': 'expense_app',
    }
    for name, value in expected.items():
        if values.get(name) and values[name] != value:
            raise SystemExit(f'{name} has a custom value in .env. Setup stopped to preserve it.')

    password = values.get('DB_PASSWORD')
    if not password or password == 'replace-with-your-database-password':
        password = secrets.token_urlsafe(32)

    root_password = getpass('MySQL root password (Enter if none was set): ')
    connection_options = {'host': '127.0.0.1'}
    if Path('/tmp/mysql.sock').exists():
        connection_options = {'unix_socket': '/tmp/mysql.sock'}

    # Do not change the password of an existing database user.
    with pymysql.connect(user='root', password=root_password,
                         autocommit=True, **connection_options) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                'CREATE DATABASE IF NOT EXISTS expense_tracker '
                'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
            cursor.execute(
                "SELECT COUNT(*) FROM mysql.user "
                "WHERE User='expense_app' AND Host='localhost'"
            )
            if not cursor.fetchone()[0]:
                cursor.execute(
                    "CREATE USER 'expense_app'@'localhost' IDENTIFIED BY %s",
                    (password,),
                )
                # Save immediately so credentials are retained if a later step fails.
                set_key(str(env), 'DB_PASSWORD', password)
            cursor.execute(
                'GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, REFERENCES, INDEX '
                "ON expense_tracker.* TO 'expense_app'@'localhost'"
            )

    # Verify the app's connection before marking setup as complete.
    with pymysql.connect(host='127.0.0.1', user='expense_app', password=password,
                         database='expense_tracker') as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')

    for name, value in {**expected, 'DB_PASSWORD': password}.items():
        set_key(str(env), name, value)
    if not values.get('SECRET_KEY') or values['SECRET_KEY'] == 'replace-with-a-long-random-secret':
        set_key(str(env), 'SECRET_KEY', secrets.token_hex(32))
    env.chmod(0o600)
    print('MySQL connection verified. Credentials saved privately in .env.')
    print('Next: flask --app app init-db')


if __name__ == '__main__':
    try:
        main()
    except pymysql.MySQLError as error:
        raise SystemExit(
            f'MySQL setup failed (error {error.args[0]}). Check that MySQL is running, '
            'the root password is correct, and .env has the correct password '
            'if expense_app already exists. Existing passwords were not changed.'
        ) from None
