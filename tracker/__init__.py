import os
import secrets
from datetime import timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, abort, request, session
from sqlalchemy.engine import URL
from .models import db


def inr(value):
    """Format rupees with Indian digit grouping, preserving paise."""
    whole, fraction = f"{value:,.2f}".replace(",", "").split(".")
    tail, head = whole[-3:], whole[:-3]
    groups = []
    while head:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return "₹" + ",".join(groups + [tail]) + "." + fraction


def create_app(test_config=None):
    load_dotenv()
    root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=URL.create("mysql+pymysql", username=os.getenv("DB_USER", "expense_app"),
            password=os.getenv("DB_PASSWORD", ""), host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")), database=os.getenv("DB_NAME", "expense_tracker")),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("Set SECRET_KEY in .env first. See README.md for setup.")
    db.init_app(app)
    app.jinja_env.filters["inr"] = inr

    @app.before_request
    def csrf_protection():
        if request.method == "POST":
            token = session.get("csrf_token")
            if not token or not secrets.compare_digest(token, request.form.get("csrf_token", "")):
                abort(400, description="Your form session expired. Reload the page and try again.")

    @app.context_processor
    def template_helpers():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return {"csrf_token": session["csrf_token"]}

    from .routes import bp
    app.register_blueprint(bp)

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables in the configured MySQL database."""
        db.create_all()
        click.echo("Database tables are ready. Open the app to create your account.")

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        from flask import render_template
        return render_template("error.html", error=error), error.code

    return app
