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
