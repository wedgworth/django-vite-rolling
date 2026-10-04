import re
import typing
from urllib.parse import urljoin

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from django_vite_rolling.conf import get_setting
from django_vite_rolling.manifest import get_manifest


if typing.TYPE_CHECKING:  # pragma: no cover
    from django.utils.safestring import SafeString


register = template.Library()


def _is_absolute_url(url: str) -> bool:
    return re.match("^https?://", url) is not None


def _dev_server_root(request=None) -> str:
    host = get_setting("dev_server_host")
    if host is None:
        host = "localhost"
        if request is not None:
            host = request.get_host().split(":")[0]
    port = get_setting("dev_server_port")
    static_path = get_setting("dev_server_static_path")
    return f"http://{host}:{port}{static_path}"


def vite_manifest(entries_names: typing.Sequence[str], request=None) -> tuple[list[str], list[str]]:
    if settings.DEBUG:
        dev_root = _dev_server_root(request)
        scripts = [f"{dev_root}/@vite/client"] + [f"{dev_root}/{name}" for name in entries_names]
        return scripts, []

    manifest = get_manifest()
    seen: set[str] = set()

    def _process(names: typing.Sequence[str]) -> tuple[list[str], list[str]]:
        scripts: list[str] = []
        styles: list[str] = []
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            chunk = manifest[name]
            import_scripts, import_styles = _process(chunk.get("imports", []))
            scripts.extend(import_scripts)
            styles.extend(import_styles)
            scripts.append(chunk["file"])
            styles.extend(chunk.get("css", []))
        return scripts, styles

    return _process(entries_names)


@register.simple_tag(name="vite_styles", takes_context=True)
def vite_styles(context, *entries_names: str) -> "SafeString":
    request = context.get("request")
    _, styles = vite_manifest(entries_names, request=request)
    hrefs = (href if _is_absolute_url(href) else static(href) for href in styles)
    return mark_safe("\n".join(f'<link rel="stylesheet" href="{href}" />' for href in hrefs))  # nosec


def _script_url(path: str) -> str:
    # Not static(): chunks import each other by Vite's file name, which already has a content hash. A storage
    # that adds its own hash (ManifestStaticFilesStorage, whitenoise) would make the browser fetch and run a
    # second copy of each module.
    return path if _is_absolute_url(path) else urljoin(settings.STATIC_URL, path)


@register.simple_tag(name="vite_scripts", takes_context=True)
def vite_scripts(context, *entries_names: str) -> "SafeString":
    request = context.get("request")
    scripts, _ = vite_manifest(entries_names, request=request)
    if settings.DEBUG:
        entries, preloads = scripts, []
    else:
        # The entries import their chunks; preload those so the browser fetches them in parallel.
        manifest = get_manifest()
        entries = [manifest[name]["file"] for name in entries_names]
        preloads = [src for src in scripts if src not in entries]
    tags = [f'<link rel="modulepreload" href="{_script_url(src)}" />' for src in preloads]
    tags += [f'<script type="module" src="{_script_url(src)}"></script>' for src in entries]
    return mark_safe("\n".join(tags))  # nosec
