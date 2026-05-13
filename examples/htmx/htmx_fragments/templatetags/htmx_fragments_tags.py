"""Template tag helpers for the htmx_fragments app.

These are intentionally tiny — they exist because the template language can't
naturally build dotted paths like ``"0.2.1"`` or look up registry metadata
keyed on the field's label.
"""

from django import template
from django.conf import settings

from multiseek.logic import get_registry

register = template.Library()


@register.filter
def dotted_path_id(path):
    """Turn a dotted path ``"0.2.1"`` into a DOM-safe id suffix ``"0-2-1"``."""
    return path.replace(".", "-")


@register.filter
def append_index(path, idx):
    """Append an index segment to a dotted path."""
    return "%s.%d" % (path, idx)


@register.filter
def parent_path(path):
    """``"0.2.3"`` -> ``"0.2"``. Root path ``"0"`` is returned unchanged
    (the root has no parent; callers that target #frame-{parent} land on
    the root in that case, which is intentional)."""
    parts = path.split(".")
    if len(parts) <= 1:
        return path
    return ".".join(parts[:-1])


def _registry():
    return get_registry(settings.MULTISEEK_REGISTRY)


@register.filter
def field_def(field_dict):
    """Look up the QueryObject for a field dict from session."""
    return _registry().get_field_by_name(field_dict.get("field", ""))


@register.filter
def field_inner_type(field_dict):
    f = _registry().get_field_by_name(field_dict.get("field", ""))
    return f.type if f is not None else None


@register.filter
def field_ops_for_field(field_dict):
    f = _registry().get_field_by_name(field_dict.get("field", ""))
    return [str(op) for op in f.ops] if f is not None else []


@register.inclusion_tag("htmx_fragments/value_widget.html")
def render_value_widget(field, field_path):
    """Render the type-specific value widget for ``field`` at ``field_path``.

    Used when walking the form_data tree in templates (frame.html →
    field.html) — the per-field, type-specific context (range_min,
    value_list, date_iso, …) wouldn't otherwise be computed. Fragment
    endpoints in views.py compute the same context directly; both paths
    end up calling ``value_widget_context``.
    """
    from htmx_fragments.views import value_widget_context

    f = _registry().get_field_by_name(field.get("field", ""))
    ctx = {
        "field": field,
        "field_path": field_path,
        "field_inner_type": f.type if f is not None else None,
    }
    ctx.update(value_widget_context(field, f))
    return ctx
