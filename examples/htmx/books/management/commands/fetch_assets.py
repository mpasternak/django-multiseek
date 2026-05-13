"""Download the htmx variant's frontend dependencies into static/vendor/.

Run this once during setup (or in CI) so the templates can reference
`{% static 'vendor/...' %}` instead of public CDNs — useful on offline
networks, restricted CI runners, or for reproducible builds.
"""

import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

# (url, relative_dest_path)
ASSETS = [
    (
        "https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js",
        "vendor/htmx/htmx.min.js",
    ),
]


class Command(BaseCommand):
    help = "Download frontend JS/CSS deps into static/vendor/ for offline / CI use."

    def handle(self, *args, **options):
        base = os.path.join(settings.BASE_DIR, "static", "multiseek")
        for url, rel in ASSETS:
            dest = os.path.join(base, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest):
                self.stdout.write(f"  ✓ {rel} (already present)")
                continue
            self.stdout.write(f"  ↓ {url} → {rel}")
            req = urllib.request.Request(url, headers={"User-Agent": "django-multiseek fetch_assets"})
            with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        self.stdout.write(self.style.SUCCESS(f"Fetched {len(ASSETS)} asset(s) into {base}"))
