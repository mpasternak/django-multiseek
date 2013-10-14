# -*- encoding: utf-8 -*-
from multiseek.logic import Ordering, ReportType

from multiseek.logic import AutocompleteQueryObject, StringQueryObject, \
    RangeQueryObject, create_registry, ValueListQueryObject, IntegerQueryObject

from models import Author, Book, Language

from django.utils.translation import ugettext_lazy as _


class TitleQueryObject(StringQueryObject):
    field_name = 'title'
    label = _("Title")


class AuthorQueryObject(AutocompleteQueryObject):
    label = _("Author")
    model = Author
    field_name = "authors"
    url = '/autocomplete/AuthorAutocompleteAuthor/'


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

registry = create_registry(
    Book,
    TitleQueryObject(),
    AuthorQueryObject(),
    YearQueryObject(),
    LanguageQueryObject(),
    CostQueryObject(),
    ordering=[
        Ordering("", _("(nothing)")),
        Ordering("title", _("title")),
        Ordering("author", _("author")),
        Ordering("year", _("year")),
    ],
    report_types=[
        ReportType("list", _("list")),
        ReportType("table", _("table")),
        ReportType("secret", _("secret"), public=False)
    ])