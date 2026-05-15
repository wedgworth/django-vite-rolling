from django.test import override_settings

from django_vite_rolling.conf import get_cache_key, get_release_version, get_setting


def test_get_setting_returns_default_when_not_configured():
    assert get_setting("cache_key_prefix") == "vite_manifest"


@override_settings(VITE={"cache_key_prefix": "custom_prefix"})
def test_get_setting_returns_user_override():
    assert get_setting("cache_key_prefix") == "custom_prefix"


@override_settings(RELEASE_VERSION="abc123")
def test_get_release_version_reads_default_setting():
    assert get_release_version() == "abc123"


@override_settings(RELEASE_VERSION="")
def test_get_release_version_blank_is_empty():
    assert get_release_version() == ""


@override_settings(RELEASE_VERSION="v1.2.3")
def test_get_cache_key_with_version():
    assert get_cache_key() == "vite_manifest:v1.2.3"


@override_settings(RELEASE_VERSION="")
def test_get_cache_key_without_version_falls_back_to_prefix():
    assert get_cache_key() == "vite_manifest"


@override_settings(MY_VERSION="x", VITE={"version_setting": "MY_VERSION"})
def test_version_setting_is_configurable():
    assert get_release_version() == "x"
