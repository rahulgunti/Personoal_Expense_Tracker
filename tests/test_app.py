"""Request-level tests use a disposable SQLite database, never personal MySQL data."""
from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import event
from tracker import create_app, inr
from tracker.models import Category, Expense, User, db


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-only", "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, path, data=None):
    client.get('/login')
    with client.session_transaction() as session:
        token = session['csrf_token']
    return client.post(path, data={**(data or {}), 'csrf_token': token}, follow_redirects=True)


def register(client, email='asha@example.com'):
    return post(client, '/register', {'name': 'Asha', 'email': email, 'password': 'capstone-pass'})


def payload(**changes):
    data = {'description': 'Weekly groceries', 'amount': '1250.50', 'expense_date': date.today().isoformat(),
            'category_id': str(db.session.scalar(db.select(Category.id))), 'payment_method': 'UPI'}
    return {**data, **changes}


def test_authentication_and_pages(client):
    assert client.get('/').status_code == 302
    assert register(client).status_code == 200
    user = db.session.scalar(db.select(User))
    assert user.password_hash != 'capstone-pass'
    assert db.session.query(Category).count() == 8
    for path in ['/', '/expenses', '/categories', '/expenses/new']:
        assert client.get(path).status_code == 200
    post(client, '/logout')
    bad = post(client, '/login', {'email': user.email, 'password': 'wrong'})
    assert b'incorrect' in bad.data
    assert post(client, '/login', {'email': user.email, 'password': 'capstone-pass'}).status_code == 200
    assert client.get('/').status_code == 200


def test_crud_dashboard_filters_and_export(client):
    register(client)
    assert b'Expense saved' in post(client, '/expenses/new', payload()).data
    entry = db.session.scalar(db.select(Expense))
    assert entry.amount == Decimal('1250.50')
    assert '₹1,250.50' in client.get('/').text
    assert b'Weekly groceries' in client.get('/expenses?q=Weekly').data
    assert b'Weekly groceries' not in client.get('/expenses?q=Missing').data
    assert b'Weekly groceries' not in client.get('/expenses?month=2001-01').data
    response = client.get('/expenses/export?q=Weekly')
    assert '1250.50' in response.text and 'Amount (INR)' in response.text
    post(client, f'/expenses/{entry.id}/edit', payload(amount='500.25'))
    assert db.session.get(Expense, entry.id).amount == Decimal('500.25')
    assert '₹500.25' in client.get('/').text
    post(client, f'/expenses/{entry.id}/delete')
    assert db.session.query(Expense).count() == 0


@pytest.mark.parametrize('amount', ['0', '-1', 'NaN', 'Infinity', 'bad', '1.001', '10000000000', '1e99999'])
def test_invalid_amount_does_not_save(client, amount):
    register(client)
    response = post(client, '/expenses/new', payload(amount=amount))
    assert response.status_code == 200
    assert db.session.query(Expense).count() == 0


def test_categories_and_inline_creation(client):
    register(client)
    post(client, '/categories', {'name': 'Education'})
    post(client, '/categories', {'name': 'education'})
    assert db.session.query(Category).count() == 9
    post(client, '/expenses/new', payload(category_id='', new_category='Pets'))
    assert db.session.scalar(db.select(Expense)).category.name == 'Pets'
    assert b'Pets' in client.get('/categories').data
    assert b'Pets' in client.get('/expenses/new').data


def test_user_isolation_and_csrf(client, app):
    register(client)
    post(client, '/expenses/new', payload())
    entry = db.session.scalar(db.select(Expense))
    entry_id, category_id = entry.id, entry.category_id
    other = app.test_client()
    register(other, 'other@example.com')
    assert b'Weekly groceries' not in other.get('/expenses').data
    assert b'Weekly groceries' not in other.get('/expenses/export').data
    assert other.get(f'/expenses/{entry_id}/edit').status_code == 404
    assert post(other, f'/expenses/{entry_id}/delete').status_code == 404
    post(other, '/expenses/new', payload(category_id=str(category_id)))
    assert db.session.query(Expense).count() == 1
    assert client.post('/expenses/new', data=payload()).status_code == 400


def test_invalid_dates_payment_and_duplicate_account(client):
    register(client)
    post(client, '/expenses/new', payload(expense_date=(date.today()+timedelta(days=1)).isoformat()))
    post(client, '/expenses/new', payload(payment_method='invalid'))
    assert db.session.query(Expense).count() == 0
    assert client.get('/?month=wrong').status_code == 400
    post(client, '/logout')
    assert b'already registered' in register(client).data
    assert db.session.query(User).count() == 1


def test_indian_grouping_and_csv_safety(client):
    assert inr(Decimal('12345678.90')) == '₹1,23,45,678.90'
    register(client)
    post(client, '/expenses/new', payload(description='=1+1'))
    assert "'=1+1" in client.get('/expenses/export').text
