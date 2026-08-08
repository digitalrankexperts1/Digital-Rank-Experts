"""
Digital Rank Experts application entry point.

Development:
    python app.py

Flask CLI:
    flask --app app.py run

Production:
    gunicorn "app:create_app()"
"""

import os

from app import create_app
from app.extensions import db


# Create Flask application.
app = create_app(
    os.environ.get(
        "FLASK_ENV",
        "production"
    )
)


@app.shell_context_processor
def make_shell_context():
    """
    Make commonly used objects available
    inside `flask shell`.
    """

    from app import models

    return {
        "db": db,
        "models": models,
    }


if __name__ == "__main__":

    debug_mode = app.config.get(
        "DEBUG",
        False
    )

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
