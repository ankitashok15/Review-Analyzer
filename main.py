"""Vercel zero-config entrypoint — serves all routes at domain root (/health, /api/v1/*, /docs)."""

from src.api.main import app

__all__ = ["app"]
