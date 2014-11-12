# -*- encoding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from logic import BooleanQueryObject

from multiseek.logic import Ordering, ReportType, DateQueryObject
from multiseek.logic import AutocompleteQueryObject, StringQueryObject, \
    RangeQueryObject, create_registry, ValueListQueryObject, IntegerQueryObject
from test_app.models import Author, Book, Language


class TitleQueryObject(StringQueryObject):
    field_name = 'title'
    label = _("Title")


class AuthorQueryObject(AutocompleteQueryObject):
    label = _("Author")
    model = Author
    field_name = "authors"
    search_fields = ['first_name', 'last_name']


class YearQueryObject(RangeQueryObject):
    field_name = "year"
    label = _("Year")


class LanguageQueryObject(ValueListQueryObject):
    field_name = 'language__name'
    values = Language.objects.all()
    label = _("Language")


class CostQueryObject(IntegerQueryObject):
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
    CostQueryObject(),
    DateLastUpdatedQueryObject(),
    AvailableQueryObject(),
    ordering=[
        Ordering("", _("(nothing)")),
        Ordering("title", _("title")),
        Ordering("authors", _("author")),
        Ordering("year", _("year")),
    ],
    default_ordering=['-title', 'authors', 'year'],
    report_types=[
        ReportType("list", _("list")),
        ReportType("table", _("table")),
        ReportType("secret", _("secret"), public=False)
    ])