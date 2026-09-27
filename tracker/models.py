"""Three small relational models. See database/README.md for the data dictionary."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "name"), db.UniqueConstraint("id", "user_id"))


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default="UPI")
    category = db.relationship("Category", foreign_keys=[category_id, user_id])
    __table_args__ = (
        db.ForeignKeyConstraint(["category_id", "user_id"], ["categories.id", "categories.user_id"]),
        db.CheckConstraint("amount > 0", name="positive_amount"),
        db.CheckConstraint("payment_method IN ('UPI', 'Cash', 'Debit card', 'Credit card', 'Bank transfer')", name="valid_payment"),
        db.Index("ix_expenses_user_date", "user_id", "expense_date"),
    )
