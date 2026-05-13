"""Seed the demo database with example Books, Authors and Languages.

This is self-contained (no model_bakery dependency) so the example project
can be set up with just `Django` and `django-multiseek` installed.
"""

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from books.models import Author, Book, Language


class Command(BaseCommand):
    help = "Populate the database with demo data (Books, Authors, Languages)."

    @transaction.atomic
    def handle(self, *args, **options):
        # Languages
        english, _ = Language.objects.get_or_create(
            name="english",
            defaults={"description": "English language"},
        )
        Language.objects.get_or_create(
            name="polish",
            defaults={"description": "Polish language"},
        )
        french, _ = Language.objects.get_or_create(
            name="french",
            defaults={"description": "French language"},
        )

        # Authors
        smith, _ = Author.objects.get_or_create(last_name="Smith", first_name="John")
        kovalsky, _ = Author.objects.get_or_create(last_name="Kovalsky", first_name="Ian")
        novak, _ = Author.objects.get_or_create(last_name="Novak", first_name="Stephan")

        # Books — main demo entries
        b1, created = Book.objects.get_or_create(
            title="A book with a title",
            defaults=dict(
                year=2013,
                language=english,
                no_editors=5,
                available=True,
            ),
        )
        if created:
            # last_updated is auto_now, but for demo realism overwrite it.
            Book.objects.filter(pk=b1.pk).update(last_updated=datetime.date(2013, 10, 22))
            b1.authors.add(smith)

        b2, created = Book.objects.get_or_create(
            title="Second book",
            defaults=dict(
                year=2000,
                language=english,
                no_editors=5,
                available=False,
            ),
        )
        if created:
            Book.objects.filter(pk=b2.pk).update(last_updated=datetime.date(2013, 9, 22))
            b2.authors.add(kovalsky)

        # Bulk seed: 50 more "Book no N" entries in French by Novak.
        for n in range(50):
            book, created = Book.objects.get_or_create(
                title="Book no %d" % n,
                defaults=dict(
                    year=1999,
                    language=french,
                    no_editors=1,
                    available=False,
                ),
            )
            if created:
                book.authors.add(novak)

        self.stdout.write(
            self.style.SUCCESS(
                "Initial data ready: %d languages, %d authors, %d books."
                % (Language.objects.count(), Author.objects.count(), Book.objects.count())
            )
        )
