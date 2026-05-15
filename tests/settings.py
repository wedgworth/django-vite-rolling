SECRET_KEY = "test"
DEBUG = False
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django_vite_rolling",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

STATIC_URL = "/static/"
USE_TZ = True

RELEASE_VERSION = "test-version"

VITE = {
    "manifest_path": None,
    "cache": True,
}
