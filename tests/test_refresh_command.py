from io import StringIO
from unittest.mock import patch

import fakeredis
from django.core.management import call_command
from django.test import override_settings


def _fake_client():
    return fakeredis.FakeRedis()


def test_command_warns_when_release_version_empty(manifest_file):
    out = StringIO()
    with override_settings(RELEASE_VERSION="", VITE={"manifest_path": str(manifest_file)}):
        call_command("refresh_vite_manifest", stdout=out)
    output = out.getvalue()
    assert "RELEASE_VERSION is empty" in output
    assert "Vite manifest cached" in output


def test_command_records_version_and_caches_manifest(manifest_file):
    client = _fake_client()
    out = StringIO()
    with override_settings(RELEASE_VERSION="v1", VITE={"manifest_path": str(manifest_file)}):
        with patch("django_vite_rolling.management.commands.refresh_vite_manifest.get_redis_connection",
                   return_value=client):
            call_command("refresh_vite_manifest", stdout=out)
    versions = [v.decode("utf-8") for v in client.lrange("recent-manifest-versions", 0, -1)]
    assert versions == ["v1"]
    assert "Vite manifest cached" in out.getvalue()


def test_command_deletes_stale_versioned_keys(manifest_file):
    client = _fake_client()
    client.set("vite_manifest:old1", b"stale")
    client.set("vite_manifest:old2", b"stale")
    client.set("vite_manifest:keep", b"current")
    client.lpush("recent-manifest-versions", b"keep")

    out = StringIO()
    with override_settings(RELEASE_VERSION="new", VITE={"manifest_path": str(manifest_file), "versions_to_keep": 2}):
        with patch("django_vite_rolling.management.commands.refresh_vite_manifest.get_redis_connection",
                   return_value=client):
            call_command("refresh_vite_manifest", stdout=out)

    # "new" and "keep" should both be retained (versions_to_keep=2)
    versions = {v.decode("utf-8") for v in client.lrange("recent-manifest-versions", 0, -1)}
    assert versions == {"new", "keep"}
    assert client.get("vite_manifest:old1") is None
    assert client.get("vite_manifest:old2") is None
    assert client.get("vite_manifest:keep") == b"current"


def test_command_trims_to_versions_to_keep(manifest_file):
    client = _fake_client()
    for v in ["a", "b", "c", "d", "e"]:
        client.lpush("recent-manifest-versions", v.encode("utf-8"))

    with override_settings(RELEASE_VERSION="f", VITE={"manifest_path": str(manifest_file), "versions_to_keep": 3}):
        with patch("django_vite_rolling.management.commands.refresh_vite_manifest.get_redis_connection",
                   return_value=client):
            call_command("refresh_vite_manifest", stdout=StringIO())

    versions = [v.decode("utf-8") for v in client.lrange("recent-manifest-versions", 0, -1)]
    assert len(versions) == 3
    assert versions[0] == "f"
