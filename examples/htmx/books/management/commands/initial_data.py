"""Seeds the database with a handful of books, authors, and languages.

Idempotent: re-running will not create duplicates.
"""
import datetime

from django.core.management.base import BaseCommand

from books.models import Author, Book, Language


class Command(BaseCommand):
    help = "Populate the demo database with sample books, authors, and languages."

    def handle(self, *args, **options):
        english, _ = Language.objects.get_or_create(
            name="english", defaults={"description": "English language"}
        )
        polish, _ = Language.objects.get_or_create(
            name="polish", defaults={"description": "Polish language"}
        )
        french, _ = Language.objects.get_or_create(
            name="french", defaults={"description": "French language"}
        )

        smith, _ = Author.objects.get_or_create(last_name="Smith", first_name="John")
        kovalsky, _ = Author.objects.get_or_create(last_name="Kovalsky", first_name="Ian")
        novak, _ = Author.objects.get_or_create(last_name="Novak", first_name="Stephan")

        if not Book.objects.filter(title="A book with a title").exists():
            b1 = Book.objects.create(
                title="A book with a title",
                year=2013,
                language=english,
                no_editors=5,
                available=True,
            )
            b1.last_updated = datetime.date(2013, 10, 22)
            b1.save()
            b1.authors.add(smith)

        if not Book.objects.filter(title="Second book").exists():
            b2 = Book.objects.create(
                title="Second book",
                year=2000,
                language=english,
                no_editors=5,
                available=False,
            )
            b2.last_updated = datetime.date(2013, 9, 22)
            b2.save()
            b2.authors.add(kovalsky)

        for i in range(50):
            title = "Book no %i" % i
            if Book.objects.filter(title=title).exists():
                continue
            b = Book.objects.create(
                title=title,
                year=1999,
                language=french,
                no_editors=0,
                available=False,
            )
            b.authors.add(novak)

        # Silence "unused" linter warnings; polish exists so the user can
        # exercise the language value-list dropdown.
        _ = polish

        self.stdout.write(self.style.SUCCESS(
            "Initial data loaded: %d books, %d authors, %d languages."
            % (Book.objects.count(), Author.objects.count(), Language.objects.count())
        ))
