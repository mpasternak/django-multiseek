"""Download the Bootstrap variant's frontend deps to static/vendor/.

Run this once during setup (or in CI) so the templates can reference
`{% static 'multiseek/vendor/...' %}` instead of public CDNs.
"""

import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

ASSETS = [
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "vendor/bootstrap/bootstrap.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "vendor/bootstrap/bootstrap.bundle.min.js",
    ),
    (
        "https://code.jquery.com/jquery-3.7.1.min.js",
        "vendor/jquery/jquery-3.7.1.min.js",
    ),
    (
        "https://code.jquery.com/ui/1.13.2/jquery-ui.min.js",
        "vendor/jquery-ui/jquery-ui.min.js",
    ),
    (
        "https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.min.css",
        "vendor/jquery-ui/jquery-ui.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css",
        "vendor/flatpickr/flatpickr.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.js",
        "vendor/flatpickr/flatpickr.min.js",
    ),
    (
        "https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/css/select2.min.css",
        "vendor/select2/select2.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/js/select2.full.min.js",
        "vendor/select2/select2.full.min.js",
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
            self.stdout.write(f"  ↓ {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "django-multiseek fetch_assets"})
            with urllib.request.urlopen(req) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        self.stdout.write(self.style.SUCCESS(f"Fetched {len(ASSETS)} asset(s) into {base}"))
