from datetime import timedelta

import dj_database_url
import environ

from .base import *  # noqa 403

print(f"\n======Loading {GENERAL_SETTINGS.ENVIRONMENT} settings...=======\n")  # noqa 403

env = environ.Env()

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(days=30)  # noqa 405
FRONTEND_URL = "http://localhost:8080"

ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

PAYSTACK_SECRET_KEY = env("PAYSTACK_TEST_SECRET_KEY")

DATABASES = {
    "default": {
        **dj_database_url.config(conn_max_age=600, conn_health_checks=True),
        "TIMEZONE": "UTC",
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "client_encoding": "UTF8",
        },
    }
}
