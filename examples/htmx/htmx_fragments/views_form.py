"""Replacement for ``multiseek.views.MultiseekFormPage`` for the htmx
variant.

The bundled page builds a JavaScript-init blob for the in-browser jQuery
widget tree. For htmx we don't need any of that — we just need the parsed
``form_data`` list (so the template can walk it server-side) plus enough
registry metadata for the field/operator selects.

We also make sure the session always has at least one field on first load,
so the user can see the form immediately rather than an empty container.
"""

import json

from django.conf import settings
from django.views.generic import TemplateView

from multiseek import AND, ANDNOT, OR
from multiseek.logic import get_registry
from multiseek.views import MULTISEEK_SESSION_KEY


def _ensure_initial_form(session, registry):
    """If the session has no multiseek_json yet, drop in a single default
    field so the rendered page isn't an empty box.
    """
    if session.get(MULTISEEK_SESSION_KEY):
        return
    fields = registry.get_fields()
    if not fields:
        return
    first = fields[0]
    initial = {
        "form_data": [
            None,
            {
                "field": str(first.label),
                "operator": str(first.ops[0]),
                "value": "",
                "prev_op": None,
            },
        ]
    }
    session[MULTISEEK_SESSION_KEY] = json.dumps(initial)
    session.modified = True


class HtmxMultiseekFormPage(TemplateView):
    registry = None
    template_name = "multiseek/index.html"

    def get_context_data(self, **kwargs):
        registry = get_registry(self.registry or settings.MULTISEEK_REGISTRY)
        _ensure_initial_form(self.request.session, registry)

        raw = self.request.session.get(MULTISEEK_SESSION_KEY) or json.dumps({"form_data": [None]})
        data = json.loads(raw)
        form_data = data.get("form_data") or [None]

        fields = registry.get_fields(self.request)
        current_ordering = data.get("ordering") or {}
        current_report_type = data.get("report_type", "")

        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "form_data": form_data,
                "form_data_json": raw,
                "fields": fields,
                "field_labels": [str(f.label) for f in fields],
                "field_types": {str(f.label): f.type for f in fields},
                "field_ops": {str(f.label): [str(op) for op in f.ops] for f in fields},
                "AND": AND,
                "OR": OR,
                "ANDNOT": ANDNOT,
                # Ordering + report-type UI inputs persist their choices via
                # the htmx endpoints below. Surface the registry's options
                # plus the current selection so the selects round-trip.
                "ordering_options": list(registry.ordering or []),
                "report_types": registry.get_report_types(self.request),
                "current_order_index": current_ordering.get("order_0", "0"),
                "current_order_dir": current_ordering.get("order_0_dir", ""),
                "current_report_type": current_report_type,
            }
        )
        return ctx
