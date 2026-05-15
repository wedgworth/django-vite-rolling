import json
import typing

from django.core.cache import cache

from django_vite_rolling.conf import get_cache_key, get_setting


if typing.TYPE_CHECKING:  # pragma: no cover
    ChunkType = typing.TypedDict(
        "ChunkType",
        {"file": str, "css": list[str], "imports": list[str]},
        total=False,
    )
    ManifestType = typing.Mapping[str, ChunkType]


def set_manifest() -> "ManifestType":
    manifest_path = get_setting("manifest_path")
    if not manifest_path:
        raise RuntimeError("VITE['manifest_path'] is not configured")
    with open(manifest_path) as fp:
        manifest: ManifestType = json.load(fp)
    cache.set(get_cache_key(), manifest, None)
    return manifest


def get_manifest() -> "ManifestType":
    if cached := cache.get(get_cache_key()):
        if get_setting("cache"):
            return cached
    return set_manifest()
