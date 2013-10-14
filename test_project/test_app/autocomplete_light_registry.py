# -*- encoding: utf-8 -*-

import autocomplete_light
from test_app.models import Author


class AutocompleteAuthor(autocomplete_light.AutocompleteModelTemplate):
    model = 'author'

    # def choices_for_request(self):
    #     q = self.request.GET.get('q', '')
    #     choices = self.choices.filter(
    #         Q(first_name__icontains=q) | Q(last_name__icontains=q))
    #     return self.order_choices(choices)[0:self.limit_choices]

autocomplete_light.register(
    Author, AutocompleteAuthor,
    search_fields=['first_name', 'last_name'])
