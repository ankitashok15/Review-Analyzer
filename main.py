"""Vercel entrypoint — zero-config FastAPI detection looks for `app` in main.py."""

from src.api.main import app

__all__ = ["app"]
