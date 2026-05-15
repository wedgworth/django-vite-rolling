import json

import pytest
from django.core.cache import cache


SAMPLE_MANIFEST = {
    "src/main.ts": {
        "file": "assets/main-abc123.js",
        "css": ["assets/main-abc123.css"],
        "imports": ["_shared.js"],
    },
    "_shared.js": {
        "file": "assets/shared-def456.js",
        "css": ["assets/shared-def456.css"],
    },
}


@pytest.fixture
def manifest_file(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(SAMPLE_MANIFEST))
    return path


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()
