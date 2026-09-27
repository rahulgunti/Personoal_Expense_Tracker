"""Flask entry point: run with `flask --app app run --debug`."""
from tracker import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
