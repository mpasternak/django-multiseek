"""Seed the demo database with Languages, Authors and Books."""

import datetime

from django.core.management.base import BaseCommand
from model_bakery import baker

from books.models import Author, Book, Language


class Command(BaseCommand):
    help = "Seed the demo database with Languages, Authors and Books."

    def handle(self, *args, **options):
        eng = baker.make(Language, name="english", description="English language")
        baker.make(Language, name="polish", description="Polish language")
        a1 = baker.make(Author, last_name="Smith", first_name="John")
        a2 = baker.make(Author, last_name="Kovalsky", first_name="Ian")
        b1 = baker.make(
            Book,
            title="A book with a title",
            year=2013,
            language=eng,
            no_editors=5,
            last_updated=datetime.date(2013, 10, 22),
            available=True,
        )
        b2 = baker.make(
            Book,
            title="Second book",
            year=2000,
            language=eng,
            no_editors=5,
            last_updated=datetime.date(2013, 9, 22),
            available=False,
        )

        b1.authors.add(a1)
        b2.authors.add(a2)

        a3 = baker.make(Author, last_name="Novak", first_name="Stephan")
        fr = baker.make(Language, name="french", description="French language")
        for a in range(0, 50):
            b3 = baker.make(Book, title="Book no %i" % a, year=1999, language=fr)
            b3.authors.add(a3)

        self.stdout.write(self.style.SUCCESS("Initial data created."))
