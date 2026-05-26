from django.template import Context, Template
from django.test import RequestFactory, override_settings


def _render(template_source: str, request=None) -> str:
    template = Template(template_source)
    return template.render(Context({"request": request}))


@override_settings(DEBUG=True)
def test_dev_mode_emits_vite_client_and_entry():
    result = _render('{% load vite %}{% vite_scripts "src/main.ts" %}')
    assert "@vite/client" in result
    assert "localhost:3001/static/src/main.ts" in result


@override_settings(DEBUG=True)
def test_dev_mode_uses_request_host():
    rf = RequestFactory()
    request = rf.get("/", HTTP_HOST="dev.box:8000")
    result = _render('{% load vite %}{% vite_scripts "src/main.ts" %}', request=request)
    assert "dev.box:3001" in result


@override_settings(DEBUG=True, VITE={"dev_server_host": "fixed.host", "dev_server_port": 5173})
def test_dev_mode_respects_configured_host_and_port():
    result = _render('{% load vite %}{% vite_scripts "src/main.ts" %}')
    assert "fixed.host:5173" in result


def test_prod_mode_resolves_entry_and_imports(manifest_file):
    with override_settings(DEBUG=False, VITE={"manifest_path": str(manifest_file)}, RELEASE_VERSION="v1"):
        scripts = _render('{% load vite %}{% vite_scripts "src/main.ts" %}')
        # Imported chunk should come before the entry chunk
        assert scripts.index("shared-def456.js") < scripts.index("main-abc123.js")


def test_prod_mode_emits_styles(manifest_file):
    with override_settings(DEBUG=False, VITE={"manifest_path": str(manifest_file)}, RELEASE_VERSION="v1"):
        styles = _render('{% load vite %}{% vite_styles "src/main.ts" %}')
        assert "main-abc123.css" in styles
        assert "shared-def456.css" in styles
        assert 'rel="stylesheet"' in styles


def test_prod_mode_handles_circular_chunk_imports(tmp_path):
    import json
    # Rollup can produce circular references between chunks (e.g. via manualChunks).
    # Ensure we don't recurse infinitely.
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "src/main.ts": {"file": "main-abc123.js", "imports": ["_chunk-a.js"]},
        "_chunk-a.js": {"file": "chunk-a-abc123.js", "imports": ["_chunk-b.js"]},
        "_chunk-b.js": {"file": "chunk-b-abc123.js", "imports": ["_chunk-a.js"]},
    }))
    with override_settings(DEBUG=False, VITE={"manifest_path": str(path)}, RELEASE_VERSION="v1"):
        scripts = _render('{% load vite %}{% vite_scripts "src/main.ts" %}')
        assert "main-abc123.js" in scripts
        assert "chunk-a-abc123.js" in scripts
        assert "chunk-b-abc123.js" in scripts


def test_prod_mode_passes_through_absolute_urls(tmp_path):
    import json
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "src/main.ts": {"file": "https://cdn.example.com/main.js", "css": ["https://cdn.example.com/main.css"]},
    }))
    with override_settings(DEBUG=False, VITE={"manifest_path": str(path)}, RELEASE_VERSION="v1"):
        scripts = _render('{% load vite %}{% vite_scripts "src/main.ts" %}')
        assert "https://cdn.example.com/main.js" in scripts
        assert "/static/https" not in scripts
