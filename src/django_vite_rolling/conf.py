from django.conf import settings


DEFAULTS = {
    "manifest_path": None,
    "cache": True,
    "cache_key_prefix": "vite_manifest",
    "dev_server_host": None,
    "dev_server_port": 3001,
    "dev_server_static_path": "/static",
    "versions_to_keep": 5,
    "version_setting": "RELEASE_VERSION",
    "versions_redis_key": "recent-manifest-versions",
    "redis_alias": "default",
}


def get_setting(key: str):
    user_settings = getattr(settings, "VITE", {})
    return user_settings.get(key, DEFAULTS[key])


def get_release_version() -> str:
    return getattr(settings, get_setting("version_setting"), "") or ""


def get_cache_key() -> str:
    prefix = get_setting("cache_key_prefix")
    version = get_release_version()
    return f"{prefix}:{version}" if version else prefix
