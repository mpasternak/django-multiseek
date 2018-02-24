from dal import autocomplete
from django.shortcuts import redirect
from django.urls import reverse

from test_app.models import Author


def root(request):
    return redirect(reverse('multiseek:index'))


class AuthorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Author.objects.all()

        if self.q:
            qs = qs.filter(last_name__istartswith=self.q)

        return qs
