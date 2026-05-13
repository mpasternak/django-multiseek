import datetime

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):
    help = "Loads sample books, authors, languages."

    def handle(self, *args, **options):
        from books.models import Author, Book, Language

        # Idempotent: only populate when DB is empty.
        if Book.objects.exists():
            self.stdout.write("Books already present; skipping initial_data.")
            return

        eng, _created = Language.objects.get_or_create(
            name=str(_("english")), defaults={"description": "English language"}
        )
        Language.objects.get_or_create(name=str(_("polish")), defaults={"description": "Polish language"})
        fr, _created = Language.objects.get_or_create(name="french", defaults={"description": "French language"})

        a1, _created = Author.objects.get_or_create(last_name="Smith", first_name="John")
        a2, _created = Author.objects.get_or_create(last_name="Kovalsky", first_name="Ian")
        a3, _created = Author.objects.get_or_create(last_name="Novak", first_name="Stephan")

        b1 = Book.objects.create(
            title="A book with a title",
            year=2013,
            language=eng,
            no_editors=5,
            available=True,
        )
        b1.last_updated = datetime.date(2013, 10, 22)
        b1.save()

        b2 = Book.objects.create(
            title="Second book",
            year=2000,
            language=eng,
            no_editors=5,
            available=False,
        )
        b2.last_updated = datetime.date(2013, 9, 22)
        b2.save()

        b1.authors.add(a1)
        b2.authors.add(a2)

        for n in range(50):
            b = Book.objects.create(title="Book no %d" % n, year=1999, language=fr, no_editors=1)
            b.authors.add(a3)

        self.stdout.write(self.style.SUCCESS("Initial data installed."))
