from django.core.management import BaseCommand
from django_redis import get_redis_connection
from redis.exceptions import RedisError

from django_vite_rolling.conf import get_release_version, get_setting
from django_vite_rolling.manifest import set_manifest


class Command(BaseCommand):
    help = "Refresh the Vite manifest cache and prune stale versions for rolling deploys."

    def handle(self, *args, **options):
        version = get_release_version()

        if not version:
            self.stdout.write(self.style.WARNING(
                f"{get_setting('version_setting')} is empty; caching manifest without versioned cleanup."
            ))
            set_manifest()
            self.stdout.write(self.style.SUCCESS("Vite manifest cached."))
            return

        versions_to_keep = get_setting("versions_to_keep")
        prefix_match = f"{get_setting('cache_key_prefix')}:*"
        versions_key = get_setting("versions_redis_key")
        redis_alias = get_setting("redis_alias")

        try:
            client = get_redis_connection(redis_alias)
            client.lpush(versions_key, version.encode("utf-8"))
            if versions_to_keep:
                client.ltrim(versions_key, 0, versions_to_keep - 1)

            recent = {v.decode("utf-8") for v in client.lrange(versions_key, 0, -1)}
            self.stdout.write(f"Recent versions: {sorted(recent)}")

            deleted = 0
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=prefix_match, count=100)
                for key in keys:
                    key_str = key.decode("utf-8")
                    if not any(key_str.endswith(f":{v}") for v in recent):
                        client.delete(key)
                        deleted += 1
                        self.stdout.write(f"Deleted stale manifest key: {key_str}")
                if cursor == 0:
                    break

            self.stdout.write(self.style.SUCCESS(
                f"Added '{version}' to recent versions; deleted {deleted} stale key(s)."
            ))

            set_manifest()
            self.stdout.write(self.style.SUCCESS("Vite manifest cached."))
        except RedisError as e:
            self.stdout.write(self.style.ERROR(f"Redis error: {e}"))
