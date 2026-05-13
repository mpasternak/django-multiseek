import json

from dal import autocomplete
from django.shortcuts import redirect
from django.urls import reverse

from books.models import Author
from multiseek.views import MULTISEEK_SESSION_KEY, MultiseekFormPage


def root(request):
    return redirect(reverse("multiseek:index"))


class AuthorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Author.objects.all()
        if self.q:
            qs = qs.filter(last_name__istartswith=self.q)
        return qs


class AlpineMultiseekFormPage(MultiseekFormPage):
    """Adds ``form_data_json`` to the template context so Alpine can hydrate
    its reactive state from the session on page load. Without this the bundled
    page only exposes ``js_init`` (jQuery code) which Alpine cannot consume.
    """

    def get_context_data(self):
        ctx = super().get_context_data()
        raw = self.request.session.get(MULTISEEK_SESSION_KEY)
        form_data = []
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and isinstance(parsed.get("form_data"), list):
                    form_data = parsed["form_data"]
            except (TypeError, ValueError):
                pass
        ctx["form_data_json"] = json.dumps(form_data)
        return ctx
