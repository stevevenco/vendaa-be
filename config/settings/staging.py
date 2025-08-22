import os

from dotenv import load_dotenv

from .base import *  # noqa 403

print(f"\n======Loading {GENERAL_SETTINGS.ENVIRONMENT} settings...=======\n")  # noqa 403

load_dotenv()

# -----------
DEBUG = True  # change to False in production
SECURE_SSL_REDIRECT = False  # change to True in production
# -----------

CORS_ALLOW_ALL_ORIGINS = False

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa 405
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle"
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login": "7/hour",
    },
}

CORS_ALLOWED_ORIGINS = [
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/(\w+\.)*satisfactory-sheela-sten-2711061c\.koyeb\.app$",
]

CORS_ALLOW_CREDENTIALS = True

ALLOWED_HOSTS = [
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "OPTIONS": {"sslmode": "require"},
    }
}
