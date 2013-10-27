# -*- encoding: utf-8 -*-

import autocomplete_light
from test_app.models import Author


class AutocompleteAuthor(autocomplete_light.AutocompleteModelJSONP):
    model = 'author'
    search_fields = ['first_name', 'last_name']


autocomplete_light.register(Author, AutocompleteAuthor)
