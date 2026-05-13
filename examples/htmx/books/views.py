from dal import autocomplete

from books.models import Author


class AuthorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Author.objects.all()
        if self.q:
            qs = qs.filter(last_name__istartswith=self.q)
        return qs
