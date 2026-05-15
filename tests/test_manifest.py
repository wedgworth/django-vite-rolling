import pytest
from django.core.cache import cache
from django.test import override_settings

from django_vite_rolling.manifest import get_manifest, set_manifest


def test_set_manifest_loads_from_file_and_caches(manifest_file):
    with override_settings(VITE={"manifest_path": str(manifest_file)}, RELEASE_VERSION="v1"):
        result = set_manifest()
        assert "src/main.ts" in result
        assert cache.get("vite_manifest:v1") == result


def test_set_manifest_raises_when_path_unconfigured():
    with override_settings(VITE={"manifest_path": None}):
        with pytest.raises(RuntimeError, match="manifest_path"):
            set_manifest()


def test_get_manifest_returns_cached_when_cache_enabled(manifest_file):
    with override_settings(VITE={"manifest_path": str(manifest_file), "cache": True}, RELEASE_VERSION="v1"):
        first = set_manifest()
        cache.set("vite_manifest:v1", {"sentinel": {"file": "x"}}, None)
        second = get_manifest()
        assert second == {"sentinel": {"file": "x"}}
        assert second != first


def test_get_manifest_re_reads_when_cache_disabled(manifest_file):
    with override_settings(VITE={"manifest_path": str(manifest_file), "cache": False}, RELEASE_VERSION="v1"):
        set_manifest()
        cache.set("vite_manifest:v1", {"sentinel": {"file": "x"}}, None)
        result = get_manifest()
        assert "src/main.ts" in result
