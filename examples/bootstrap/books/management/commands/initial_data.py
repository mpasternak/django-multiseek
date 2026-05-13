"""Seed the demo database with a varied set of Books, Authors and Languages.

Used by all four example variants. Designed to give every multiseek field type
something interesting to filter on: multiple languages, a wide year range,
multi-author books, mixed available flags, varied last_updated dates, and
titles that overlap in different ways so the string filter has real hits.
"""

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from books.models import Author, Book, Language

LANGUAGES = [
    ("english", "English language"),
    ("polish", "Polish language"),
    ("french", "French language"),
    ("german", "German language"),
    ("spanish", "Spanish language"),
    ("italian", "Italian language"),
    ("japanese", "Japanese language"),
]

# (last_name, first_name)
AUTHORS = [
    ("Austen", "Jane"),
    ("Lem", "Stanisław"),
    ("Murakami", "Haruki"),
    ("García Márquez", "Gabriel"),
    ("Camus", "Albert"),
    ("Calvino", "Italo"),
    ("Le Guin", "Ursula K."),
    ("Tokarczuk", "Olga"),
]

# (title, year, language_idx, [author_idxs], no_editors, available, last_updated)
BOOKS = [
    ("Pride and Prejudice", 1813, 0, [0], 3, True, datetime.date(2024, 1, 15)),
    ("Sense and Sensibility", 1811, 0, [0], 2, True, datetime.date(2024, 3, 8)),
    ("Persuasion", 1817, 0, [0], 4, False, datetime.date(2024, 8, 15)),
    ("Solaris", 1961, 1, [1], 5, True, datetime.date(2024, 3, 20)),
    ("Solaris (German translation)", 1961, 3, [1], 4, False, datetime.date(2024, 10, 22)),
    ("Cyberiad", 1965, 1, [1], 4, True, datetime.date(2023, 9, 14)),
    ("The Futurological Congress", 1971, 1, [1], 3, True, datetime.date(2024, 11, 25)),
    ("Norwegian Wood", 1987, 6, [2], 7, False, datetime.date(2023, 12, 1)),
    ("Kafka on the Shore", 2002, 6, [2], 8, True, datetime.date(2024, 7, 8)),
    ("Hardboiled Wonderland and the End of the World", 1985, 6, [2], 9, True, datetime.date(2024, 12, 11)),
    ("After Dark", 2004, 6, [2], 4, False, datetime.date(2024, 5, 12)),
    ("One Hundred Years of Solitude", 1967, 4, [3], 4, True, datetime.date(2024, 2, 10)),
    ("Love in the Time of Cholera", 1985, 4, [3], 5, True, datetime.date(2024, 2, 28)),
    ("The Stranger", 1942, 2, [4], 2, True, datetime.date(2023, 11, 5)),
    ("The Plague", 1947, 2, [4], 3, True, datetime.date(2023, 10, 20)),
    ("The Myth of Sisyphus", 1942, 2, [4], 2, False, datetime.date(2023, 12, 15)),
    ("Invisible Cities", 1972, 5, [5], 1, True, datetime.date(2024, 6, 18)),
    ("Cosmicomics", 1965, 5, [5], 2, True, datetime.date(2024, 9, 12)),
    ("If on a winter's night a traveler", 1979, 5, [5], 3, True, datetime.date(2024, 6, 4)),
    ("The Left Hand of Darkness", 1969, 0, [6], 6, False, datetime.date(2024, 4, 22)),
    ("A Wizard of Earthsea", 1968, 0, [6], 5, True, datetime.date(2024, 1, 30)),
    ("The Dispossessed", 1974, 0, [6], 7, True, datetime.date(2024, 8, 30)),
    ("Flights", 2007, 1, [7], 3, True, datetime.date(2024, 5, 30)),
    ("Drive Your Plow Over the Bones of the Dead", 2009, 1, [7], 6, True, datetime.date(2024, 11, 4)),
    ("Primeval and Other Times", 1996, 1, [7], 4, True, datetime.date(2024, 4, 15)),
    # multi-author books
    ("A Conversation: Lem & Le Guin", 1990, 0, [1, 6], 5, True, datetime.date(2024, 7, 1)),
    ("Imagined Landscapes (Murakami & Calvino)", 2010, 5, [2, 5], 3, True, datetime.date(2024, 8, 22)),
]


class Command(BaseCommand):
    help = "Populate the database with the multiseek demo dataset."

    @transaction.atomic
    def handle(self, *args, **options):
        languages = []
        for name, desc in LANGUAGES:
            obj, _ = Language.objects.get_or_create(name=name, defaults={"description": desc})
            languages.append(obj)

        authors = []
        for last_name, first_name in AUTHORS:
            obj, _ = Author.objects.get_or_create(last_name=last_name, first_name=first_name)
            authors.append(obj)

        for title, year, lang_idx, author_idxs, no_editors, available, last_updated in BOOKS:
            book, created = Book.objects.get_or_create(
                title=title,
                defaults=dict(
                    year=year,
                    language=languages[lang_idx],
                    no_editors=no_editors,
                    available=available,
                ),
            )
            if created:
                # last_updated has auto_now=True on the model — bypass it
                # with a direct UPDATE so the demo has spread-out dates.
                Book.objects.filter(pk=book.pk).update(last_updated=last_updated)
                book.authors.add(*[authors[i] for i in author_idxs])

        self.stdout.write(
            self.style.SUCCESS(
                "Initial data ready: %d languages, %d authors, %d books."
                % (Language.objects.count(), Author.objects.count(), Book.objects.count())
            )
        )
