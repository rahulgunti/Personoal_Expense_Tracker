"""Routes handle forms; SQLAlchemy handles parameterized database queries."""
import csv
import io
import re
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from .models import Category, Expense, User, db

bp = Blueprint("web", __name__)
PAYMENTS = ("UPI", "Cash", "Debit card", "Credit card", "Bank transfer")
DEFAULT_CATEGORIES = ("Food & Dining", "Groceries", "Transport", "Shopping", "Bills & Utilities", "Health", "Entertainment", "Other")


@bp.before_app_request
def load_user():
    g.user = db.session.get(User, session["user_id"]) if session.get("user_id") else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("web.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        user = db.session.scalar(db.select(User).where(User.email == request.form.get("email", "").strip().lower()))
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            return redirect(url_for("web.dashboard"))
        flash("Email or password is incorrect. Please try again.", "error")
    return render_template("auth.html", register=False)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not 1 <= len(name) <= 80 or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Enter your name and a valid email address.", "error")
        elif not 8 <= len(password) <= 128:
            flash("Use a password between 8 and 128 characters.", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            try:
                db.session.flush()
                db.session.add_all(Category(user_id=user.id, name=name) for name in DEFAULT_CATEGORIES)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("This email is already registered. Sign in instead.", "error")
            else:
                session.clear()
                session["user_id"] = user.id
                session.permanent = True
                flash("Welcome! Add your first expense to get started.", "success")
                return redirect(url_for("web.dashboard"))
    return render_template("auth.html", register=True)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login"))


def categories_for_user():
    return db.session.scalars(db.select(Category).where(Category.user_id == g.user.id).order_by(Category.name)).all()


def month_window(raw):
    try:
        start = date.fromisoformat(raw + "-01")
        end = date(start.year, start.month, monthrange(start.year, start.month)[1])
        return start, end
    except ValueError:
        abort(400, description="Choose a valid month.")


@bp.route("/")
@login_required
def dashboard():
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    start, end = month_window(month)
    entries = db.session.scalars(db.select(Expense).where(Expense.user_id == g.user.id, Expense.expense_date.between(start, end)).order_by(Expense.expense_date.desc(), Expense.id.desc())).all()
    total = sum((e.amount for e in entries), Decimal("0"))
    totals = {}
    daily = [Decimal("0")] * end.day
    for e in entries:
        totals[e.category.name] = totals.get(e.category.name, Decimal("0")) + e.amount
        daily[e.expense_date.day - 1] += e.amount
    breakdown = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return render_template("dashboard.html", active="dashboard", month=month, period=start.strftime("%B %Y"),
        entries=entries[:5], total=total, count=len(entries), average=total / len(entries) if entries else 0,
        breakdown=breakdown, daily=daily, peak=max(daily) or 1)


def filtered_expenses():
    query = db.select(Expense).where(Expense.user_id == g.user.id)
    month = request.args.get("month", "")
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()[:160]
    if month:
        query = query.where(Expense.expense_date.between(*month_window(month)))
    if category:
        if not category.isdigit():
            abort(400, description="Choose a valid category.")
        query = query.where(Expense.category_id == int(category))
    if search:
        query = query.where(Expense.description.contains(search, autoescape=True))
    return query.order_by(Expense.expense_date.desc(), Expense.id.desc())


@bp.get("/expenses")
@login_required
def expenses():
    entries = db.session.scalars(filtered_expenses()).all()
    return render_template("expenses.html", active="expenses", entries=entries, categories=categories_for_user(), total=sum((e.amount for e in entries), Decimal("0")))


@bp.get("/expenses/export")
@login_required
def export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Category", "Payment method", "Amount (INR)"])
    def safe(value):
        return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value
    for e in db.session.scalars(filtered_expenses()):
        writer.writerow([e.expense_date, safe(e.description), safe(e.category.name), e.payment_method, e.amount])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=expenses.csv"})


def owned_expense(expense_id):
    return db.first_or_404(db.select(Expense).where(Expense.id == expense_id, Expense.user_id == g.user.id))


@bp.route("/expenses/new", methods=["GET", "POST"])
@bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def expense_form(expense_id=None):
    expense = owned_expense(expense_id) if expense_id is not None else None
    if request.method == "POST":
        try:
            description = request.form.get("description", "").strip()
            if not 1 <= len(description) <= 160:
                raise ValueError("Enter a description of up to 160 characters.")
            try:
                amount = Decimal(request.form.get("amount", ""))
            except InvalidOperation:
                raise ValueError("Enter a valid amount.")
            if not amount.is_finite() or not Decimal("0.01") <= amount <= Decimal("9999999999.99") or amount != amount.quantize(Decimal("0.01")):
                raise ValueError("Enter an amount from ₹0.01 to ₹9,99,99,99,999.99 with at most two decimal places.")
            try:
                expense_date = date.fromisoformat(request.form.get("expense_date", ""))
            except ValueError:
                raise ValueError("Choose a valid expense date.")
            if expense_date > date.today() or expense_date.year < 1000:
                raise ValueError("Choose a date between year 1000 and today.")
            category_id = request.form.get("category_id", "")
            category = db.session.scalar(db.select(Category).where(Category.user_id == g.user.id, Category.id == int(category_id))) if category_id.isdigit() else None
            new_category = " ".join(request.form.get("new_category", "").split())
            if len(new_category) > 40:
                raise ValueError("Category names must be 40 characters or fewer.")
            if not category and not new_category:
                raise ValueError("Choose a category or enter a new category name.")
            payment = request.form.get("payment_method")
            if payment not in PAYMENTS:
                raise ValueError("Choose a valid payment method.")
            if new_category:
                category = db.session.scalar(db.select(Category).where(Category.user_id == g.user.id, func.lower(Category.name) == new_category.lower()))
                if category is None:
                    category = Category(user_id=g.user.id, name=new_category)
                    db.session.add(category)
                    db.session.flush()
            if expense is None:
                expense = Expense(user_id=g.user.id)
                db.session.add(expense)
            expense.description, expense.amount, expense.expense_date = description, amount, expense_date
            expense.category_id, expense.payment_method = category.id, payment
            db.session.commit()
            flash("Expense saved successfully.", "success")
            return redirect(url_for("web.expenses"))
        except IntegrityError:
            db.session.rollback()
            flash("The category changed while saving. Please try again.", "error")
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("expense_form.html", active="expenses", expense=expense, categories=categories_for_user(), payments=PAYMENTS, today=date.today().isoformat())


@bp.post("/expenses/<int:expense_id>/delete")
@login_required
def delete_expense(expense_id):
    db.session.delete(owned_expense(expense_id))
    db.session.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for("web.expenses"))


@bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = " ".join(request.form.get("name", "").split())
        if not 1 <= len(name) <= 40:
            flash("Enter a category name of up to 40 characters.", "error")
        elif db.session.scalar(db.select(Category).where(Category.user_id == g.user.id, func.lower(Category.name) == name.lower())):
            flash("You already have that category.", "error")
        else:
            db.session.add(Category(user_id=g.user.id, name=name))
            try:
                db.session.commit()
                flash("Category added. It is now available in the expense dropdown.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("You already have that category.", "error")
        return redirect(url_for("web.categories"))
    rows = db.session.execute(db.select(Category, func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0)).outerjoin(Expense, (Expense.category_id == Category.id) & (Expense.user_id == Category.user_id)).where(Category.user_id == g.user.id).group_by(Category.id).order_by(Category.name)).all()
    return render_template("categories.html", active="categories", rows=rows)
