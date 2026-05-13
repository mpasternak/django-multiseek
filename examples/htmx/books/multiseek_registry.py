"""Multiseek registry for the htmx (Variant 4) example project.

Uses the public API documented in `multiseek/__init__.py`: import directly
from `multiseek` rather than from `multiseek.logic`.
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from multiseek import (
    AutocompleteQueryObject,
    BooleanQueryObject,
    DateQueryObject,
    IntegerQueryObject,
    Ordering,
    RangeQueryObject,
    ReportType,
    StringQueryObject,
    ValueListQueryObject,
    create_registry,
)

from books.models import Author, Book, Language


class TitleQueryObject(StringQueryObject):
    field_name = "title"
    label = _("Title")


class AuthorQueryObject(AutocompleteQueryObject):
    label = _("Author")
    model = Author
    field_name = "authors"
    search_fields = ["first_name", "last_name"]

    def get_url(self):
        return reverse("author-autocomplete")


class YearQueryObject(RangeQueryObject):
    field_name = "year"
    label = _("Year")


class LanguageQueryObject(ValueListQueryObject):
    field_name = "language__name"
    values = Language.objects.all
    label = _("Language")


class EditorsQueryObject(IntegerQueryObject):
    field_name = "no_editors"
    label = _("Number of editors")


class DateLastUpdatedQueryObject(DateQueryObject):
    field_name = "last_updated"
    label = _("Last updated on")


class AvailableQueryObject(BooleanQueryObject):
    field_name = "available"
    label = _("Available")


registry = create_registry(
    Book,
    TitleQueryObject(),
    AuthorQueryObject(),
    YearQueryObject(),
    LanguageQueryObject(),
    EditorsQueryObject(),
    DateLastUpdatedQueryObject(),
    AvailableQueryObject(),
    ordering=[
        Ordering("", _("(nothing)")),
        Ordering("title", _("title")),
        Ordering("authors", _("author")),
        Ordering("year", _("year")),
    ],
    default_ordering=["-title", "authors", "year"],
    report_types=[
        ReportType("list", _("list")),
    ],
)
