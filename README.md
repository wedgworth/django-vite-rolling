# django-vite-rolling

A lean Django + Vite integration with rolling-deploy-safe manifest caching.

Roughly 100 lines of code. No React Refresh, no polyfills, no legacy bundle handling — just `{% vite_scripts %}`, `{% vite_styles %}`, and a management command that keeps Vite manifest caches consistent across rolling deploys.

## Why this exists

Most Django + Vite integrations cache one manifest globally. On a rolling deploy, both the old and new app versions can serve requests simultaneously, each needing their own manifest. This package caches manifests under versioned Redis keys (`vite_manifest:<RELEASE_VERSION>`) and provides a management command to prune stale versions during deploys.

If you don't need versioned/rolling-deploy support, you probably want [`django-vite`](https://github.com/MrBin99/django-vite) instead.

## Install

```bash
pip install django-vite-rolling
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_vite_rolling",
]
```

Requires `django-redis` configured as your default cache backend.

## Configure

```python
VITE = {
    "manifest_path": BASE_DIR / "static" / ".vite" / "manifest.json",
    "cache": not DEBUG,
}
```

### All settings

| Key | Default | Description |
|---|---|---|
| `manifest_path` | *(required)* | Path to Vite's `manifest.json` |
| `cache` | `True` | Whether to cache the loaded manifest in Redis (set `False` in dev) |
| `cache_key_prefix` | `"vite_manifest"` | Redis key prefix; full key is `<prefix>:<RELEASE_VERSION>` |
| `dev_server_host` | `None` | Dev server host. `None` → derive from request `Host` header (fallback `localhost`) |
| `dev_server_port` | `3001` | Dev server port |
| `dev_server_static_path` | `"/static"` | Path prefix Vite serves from |
| `versions_to_keep` | `5` | How many recent release versions to retain manifests for |
| `version_setting` | `"RELEASE_VERSION"` | Name of the Django setting holding the current release identifier |
| `versions_redis_key` | `"recent-manifest-versions"` | Redis list key tracking recent versions |
| `redis_alias` | `"default"` | django-redis alias to use |

## Usage

In your base template:

```html
{% load vite %}
<!DOCTYPE html>
<html>
  <head>
    {% vite_styles "src/main.ts" %}
  </head>
  <body>
    {% vite_scripts "src/main.ts" %}
  </body>
</html>
```

In `DEBUG` mode the tags inject Vite's HMR client and module URLs pointing at the dev server. In production they resolve the named entries through the manifest:

- `vite_scripts` emits one `<script type="module">` per entry and a `<link rel="modulepreload">` for each chunk the entries import, so the browser fetches them in parallel.
- `vite_styles` emits a stylesheet link for the entries' CSS and the CSS of every imported chunk.

Script and preload URLs are `STATIC_URL` plus Vite's file name. They skip `static()`, because chunks import each other by Vite's file name: a storage that adds its own hash (`ManifestStaticFilesStorage`, whitenoise) would make the browser download and run each module twice. Keep Vite's default hashed file names (`[name]-[hash].js`) so these URLs change when the content does. Stylesheet URLs still go through `static()`.

## Post-deploy

Run after each deploy (e.g., in a release-phase / post-deploy hook):

```bash
python manage.py refresh_vite_manifest
```

This:
1. Records `RELEASE_VERSION` in a Redis list of recent versions (truncated to `versions_to_keep`).
2. Scans for `vite_manifest:*` keys whose suffix is not in the recent list and deletes them.
3. Loads the current manifest and caches it under `vite_manifest:<RELEASE_VERSION>`.

If `RELEASE_VERSION` is empty, the command caches the manifest under the bare prefix and skips cleanup.

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
