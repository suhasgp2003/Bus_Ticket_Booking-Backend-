"""Isolated test database; never connects to the deployed PostgreSQL database."""

from .settings import *  # noqa: F403

SECRET_KEY = "gobus-tests-only"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
