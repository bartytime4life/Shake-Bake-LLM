"""Inert synthetic source for evidence preparation; never executed by the helper."""
from server import create_app


def main():
    app = create_app()
    app.run(port=8080)
