import os

from capture_pakistan import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "false",
            ).strip().lower()
            in {"1", "true", "yes", "on"}
        ),
    )