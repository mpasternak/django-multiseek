"""Fragment views for the htmx (Variant 4) example project.

State model
===========

The canonical state lives in the user's session, under the key
``multiseek_json`` (the same key the bundled multiseek views read). It is a
JSON-encoded dict of shape::

    {"form_data": [prev_op, element_1, element_2, ...]}

Each element is either:

* A field ``dict`` with keys ``field``, ``operator``, ``value``, ``prev_op``.
* A nested ``list`` with shape ``[prev_op, ...children]`` for sub-frames.

Paths
=====

An element is identified by a dotted path. ``"0"`` is the root frame's outer
list. ``"0.1"`` is the element at index 1 of the root frame's element list
(index 0 is the ``prev_op``). ``"0.2.1"`` is the element at index 1 of the
sub-frame at index 2 of the root frame, and so on.

The path is bound into the URL as a single string and parsed back into a tuple
of integers. Each fragment view walks the tree to that path, mutates, writes
back to the session, and returns the appropriate rendered fragment.
"""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from multiseek import AND, ANDNOT, OR
from multiseek.logic import get_registry
from multiseek.views import MULTISEEK_SESSION_KEY, MultiseekResults

logger = logging.getLogger(__name__)


def _describe_shape(form_data):
    """Compact one-line description of the form_data tree, for error logs."""

    def _walk(node):
        if isinstance(node, list):
            return "[" + ", ".join(_walk(c) for c in node) + "]"
        if isinstance(node, dict):
            return "{field=%s, op=%s}" % (
                node.get("field", "?"),
                node.get("operator", "?"),
            )
        return repr(node)

    return _walk(form_data)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def _load_form(session):
    """Return the parsed form_data dict from session, creating an empty one
    on demand. Always returns a dict ``{"form_data": [None, ...]}``.
    """
    raw = session.get(MULTISEEK_SESSION_KEY)
    if not raw:
        return {"form_data": [None]}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {"form_data": [None]}
    if not isinstance(data, dict):
        data = {"form_data": data}
    if "form_data" not in data or not isinstance(data["form_data"], list):
        data["form_data"] = [None]
    return data


def _save_form(session, data):
    session[MULTISEEK_SESSION_KEY] = json.dumps(data)
    session.modified = True


# ---------------------------------------------------------------------------
# Path-addressing
# ---------------------------------------------------------------------------


def _parse_path(elpath):
    """Parse ``"0.2.1"`` -> ``[0, 2, 1]``. Empty/invalid -> ``None``."""
    if not elpath:
        return None
    try:
        return [int(p) for p in elpath.split(".") if p != ""]
    except ValueError:
        return None


def _walk(form_data, parts):
    """Walk the form_data tree following the integer indices in ``parts``.

    Returns the node found, or ``None`` if the path is invalid.

    ``parts[0]`` must always be ``0`` (the root frame). Subsequent indices
    select children. For a list node, ``children[i]`` corresponds to
    ``node[i]`` (we keep ``node[0]`` as the ``prev_op``, so element 1 is the
    first real child).
    """
    if not parts:
        return None
    if parts[0] != 0:
        return None
    node = form_data
    for idx in parts[1:]:
        if not isinstance(node, list):
            return None
        if idx < 1 or idx >= len(node):
            return None
        node = node[idx]
    return node


def _walk_parent(form_data, parts):
    """Return ``(parent_list, index_in_parent)`` for the node at ``parts``,
    or ``(None, None)`` if the path is invalid or points to the root.
    """
    if not parts or len(parts) < 2:
        return None, None
    parent = _walk(form_data, parts[:-1])
    if not isinstance(parent, list):
        return None, None
    idx = parts[-1]
    if idx < 1 or idx >= len(parent):
        return None, None
    return parent, idx


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _tree_context(registry):
    """Common template context for rendering fragments — supplies the list
    of available fields and per-field operators / types so the template can
    render selects without any JS.
    """
    fields = registry.get_fields()
    return {
        "fields": fields,
        "field_labels": [str(f.label) for f in fields],
        "field_types": {str(f.label): f.type for f in fields},
        "field_ops": {str(f.label): [str(op) for op in f.ops] for f in fields},
        "AND": AND,
        "OR": OR,
        "ANDNOT": ANDNOT,
    }


def _render_frame(request, registry, form_data, parts, prev_op):
    """Render the frame fragment at ``parts``."""
    node = _walk(form_data, parts)
    if not isinstance(node, list):
        return HttpResponseBadRequest("Path does not refer to a frame")
    ctx = _tree_context(registry)
    ctx.update(
        {
            "frame": node,
            "frame_path": ".".join(str(p) for p in parts),
            "frame_prev_op": prev_op,
            "is_root": len(parts) == 1,
        }
    )
    return render(request, "htmx_fragments/frame.html", ctx)


def value_widget_context(node, field_def):
    """Type-specific context for value_widget.html.

    Parses the stored ``value`` (which is JSON for range/date) into widget-
    friendly pieces. For value-list types, resolves ``field_def.values`` (which
    may be a list, a callable, or a queryset) into a flat list of strings.
    """
    ctx = {}
    if field_def is None:
        return ctx
    val = node.get("value") or ""
    t = field_def.type
    if t == "range":
        rmin, rmax = "", ""
        if val:
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list) and len(parsed) == 2:
                    rmin, rmax = parsed[0], parsed[1]
            except (TypeError, ValueError):
                pass
        ctx.update({"range_min": rmin, "range_max": rmax})
    elif t == "date":
        date_iso, date_iso_max = "", ""
        if val:
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    if len(parsed) >= 1:
                        date_iso = parsed[0] or ""
                    if len(parsed) >= 2:
                        date_iso_max = parsed[1] or ""
            except (TypeError, ValueError):
                pass
        ctx.update({"date_iso": date_iso, "date_iso_max": date_iso_max})
    elif t == "value-list":
        values = field_def.values
        if callable(values):
            values = values()
        ctx["value_list"] = [str(v) for v in values]
    return ctx


def _render_field(request, registry, form_data, parts):
    """Render the field fragment at ``parts``."""
    node = _walk(form_data, parts)
    if not isinstance(node, dict):
        return HttpResponseBadRequest("Path does not refer to a field")
    ctx = _tree_context(registry)
    field_label = node.get("field", "")
    field_def = registry.get_field_by_name(field_label)
    ctx.update(
        {
            "field": node,
            "field_path": ".".join(str(p) for p in parts),
            "field_def": field_def,
            "field_inner_type": field_def.type if field_def is not None else None,
            "field_ops_for_field": ([str(op) for op in field_def.ops] if field_def is not None else []),
        }
    )
    ctx.update(value_widget_context(node, field_def))
    return render(request, "htmx_fragments/field.html", ctx)


def _render_value_widget(request, registry, form_data, parts):
    node = _walk(form_data, parts)
    if not isinstance(node, dict):
        return HttpResponseBadRequest("Path does not refer to a field")
    field_label = node.get("field", "")
    field_def = registry.get_field_by_name(field_label)
    ctx = {
        "field": node,
        "field_path": ".".join(str(p) for p in parts),
        "field_def": field_def,
        "field_inner_type": field_def.type if field_def is not None else None,
    }
    ctx.update(value_widget_context(node, field_def))
    return render(request, "htmx_fragments/value_widget.html", ctx)


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------


def _default_field_entry(registry, prev_op):
    """Build a fresh field dict using the first registered field as the
    default. The session always contains a serialisable structure.
    """
    fields = registry.get_fields()
    if not fields:
        # Should never happen — a registry with zero fields is unusable.
        return {"field": "", "operator": "", "value": "", "prev_op": prev_op}
    first = fields[0]
    return {
        "field": str(first.label),
        "operator": str(first.ops[0]),
        "value": "",
        "prev_op": prev_op,
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def _registry():
    return get_registry(settings.MULTISEEK_REGISTRY)


@csrf_protect
def add_field(request, elpath):
    """POST -> append a field to the frame at ``elpath``. Returns the rendered
    field fragment.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest("Bad path")

    data = _load_form(request.session)
    frame = _walk(data["form_data"], parts)
    if not isinstance(frame, list):
        return HttpResponseBadRequest("Path does not refer to a frame")

    registry = _registry()
    # The first element of any frame's child slot has prev_op=None; subsequent
    # ones default to "and" (the bundled UI's convention).
    prev_op = None if len(frame) == 1 else AND
    frame.append(_default_field_entry(registry, prev_op))
    _save_form(request.session, data)

    new_parts = parts + [len(frame) - 1]
    return _render_field(request, registry, data["form_data"], new_parts)


@csrf_protect
def add_frame(request, elpath):
    """POST -> append a sub-frame to the frame at ``elpath``. Returns the
    rendered sub-frame fragment.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest("Bad path")

    data = _load_form(request.session)
    frame = _walk(data["form_data"], parts)
    if not isinstance(frame, list):
        return HttpResponseBadRequest("Path does not refer to a frame")

    registry = _registry()
    prev_op = None if len(frame) == 1 else AND
    # A sub-frame is itself a list: [prev_op, default_field_dict].
    new_subframe = [prev_op, _default_field_entry(registry, None)]
    frame.append(new_subframe)
    _save_form(request.session, data)

    new_parts = parts + [len(frame) - 1]
    return _render_frame(request, registry, data["form_data"], new_parts, prev_op)


@csrf_protect
def delete_element(request, elpath):
    """DELETE -> remove the element at ``elpath``.

    Returns the re-rendered PARENT frame (with hx-target on the delete button
    pointing at it). Re-rendering the parent guarantees every surviving
    sibling's data-path is rewritten, so a follow-up DELETE on a sibling
    (whose path may have shifted) doesn't 400 with a stale path.
    """
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest(f"Invalid path: {elpath!r}")
    if len(parts) < 2:
        return HttpResponseBadRequest("Cannot delete the root frame")

    data = _load_form(request.session)
    parent, idx = _walk_parent(data["form_data"], parts)
    if parent is None:
        # Path no longer addresses anything — surface a useful error so the
        # browser console / server log shows what we tried.
        msg = (
            f"Path {elpath!r} not found in form_data. Current shape: "
            f"{_describe_shape(data['form_data'])}. This usually means the "
            f"DOM held a stale path after a sibling was removed; the parent "
            f"frame should re-render on every delete so paths stay fresh."
        )
        logger.warning("htmx delete_element: %s", msg)
        return HttpResponseBadRequest(msg)

    # Don't allow removing the last remaining real element of the root frame —
    # the bundled multiseek UI enforces the same invariant.
    if len(parts) == 2 and len(parent) <= 2:
        return HttpResponse(
            "<small>Cannot remove the last field.</small>",
            status=200,
            headers={"HX-Reswap": "none"},
        )

    parent.pop(idx)

    # If the element we just removed was at position 1 and the new position-1
    # element still has a ``prev_op``, normalise it to None — the first
    # element of a frame must have prev_op=None.
    if idx == 1 and len(parent) >= 2:
        first = parent[1]
        if isinstance(first, dict):
            first["prev_op"] = None
        elif isinstance(first, list) and first:
            first[0] = None

    _save_form(request.session, data)

    # Re-render the parent frame so every surviving child's path is fresh.
    registry = _registry()
    parent_parts = parts[:-1]
    parent_frame = _walk(data["form_data"], parent_parts)
    # parent_prev_op is the parent frame's own prev_op (only meaningful for
    # non-root frames). _render_frame ignores it when is_root=True.
    parent_prev_op = parent_frame[0] if len(parent_parts) > 1 else None
    return _render_frame(request, registry, data["form_data"], parent_parts, parent_prev_op)


@csrf_protect
def change_field_type(request, elpath):
    """POST -> the user picked a different field type from the type select.

    The new field label is taken from POST['field']. We update the session
    (resetting operator to the field's first op and value to empty) and
    return the rendered value widget for the new type.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest("Bad path")

    new_field_label = request.POST.get("field", "")
    if not new_field_label:
        return HttpResponseBadRequest("Missing 'field'")

    registry = _registry()
    field_def = registry.get_field_by_name(new_field_label)
    if field_def is None:
        return HttpResponseBadRequest("Unknown field")

    data = _load_form(request.session)
    node = _walk(data["form_data"], parts)
    if not isinstance(node, dict):
        return HttpResponseBadRequest("Path does not refer to a field")

    node["field"] = new_field_label
    node["operator"] = str(field_def.ops[0])
    node["value"] = ""
    _save_form(request.session, data)

    # Return the full re-rendered field fragment so the operator select
    # (which depends on the field type) also refreshes. htmx swaps the entire
    # field row via hx-target/outerHTML.
    return _render_field(request, registry, data["form_data"], parts)


@csrf_protect
def set_field_value(request, elpath):
    """POST -> store the user-edited value/operator in the session.

    For most field types ``value`` arrives directly in POST. For range and
    date types the widget posts split inputs (``value_min``/``value_max`` or
    ``value_date``/``value_date_max``) that we combine into the JSON shape
    multiseek's QueryObjects expect.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest("Bad path")

    data = _load_form(request.session)
    node = _walk(data["form_data"], parts)
    if not isinstance(node, dict):
        return HttpResponseBadRequest("Path does not refer to a field")

    if "operator" in request.POST:
        node["operator"] = request.POST["operator"]

    field_def = _registry().get_field_by_name(node.get("field", ""))
    field_type = field_def.type if field_def else None

    if field_type == "range":
        vmin = request.POST.get("value_min", "")
        vmax = request.POST.get("value_max", "")
        try:
            node["value"] = json.dumps([int(vmin), int(vmax)])
        except (TypeError, ValueError):
            # Either bound missing or non-integer — leave value empty so
            # impacts_query() drops the clause rather than erroring.
            node["value"] = ""
    elif field_type == "date":
        d1 = request.POST.get("value_date", "")
        d2 = request.POST.get("value_date_max", "")
        if d1 and d2:
            node["value"] = json.dumps([d1, d2])
        elif d1:
            node["value"] = json.dumps([d1])
        elif d2:
            node["value"] = json.dumps([d2])
        else:
            node["value"] = ""
    elif "value" in request.POST:
        node["value"] = request.POST["value"]

    _save_form(request.session, data)
    return HttpResponse("")


@csrf_protect
def set_field_prev_op(request, elpath):
    """POST -> store the user-changed prev_op (and/or/andnot) on a field or
    sub-frame.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    parts = _parse_path(elpath)
    if parts is None:
        return HttpResponseBadRequest("Bad path")

    prev_op = request.POST.get("prev_op", "")
    if prev_op not in (AND, OR, ANDNOT):
        return HttpResponseBadRequest("Bad prev_op")

    data = _load_form(request.session)
    node = _walk(data["form_data"], parts)
    if isinstance(node, dict):
        node["prev_op"] = prev_op
    elif isinstance(node, list) and node:
        node[0] = prev_op
    else:
        return HttpResponseBadRequest("Bad path")
    _save_form(request.session, data)
    return HttpResponse("")


def results_fragment(request):
    """Return ONLY the inner results HTML (no <html> wrapper).

    Invoked by the htmx Send Query button via ``hx-get`` so the results
    swap into a div under the form, matching the iframe-based UX of the
    other variants. The bundled /multiseek/results/ URL is still
    available for direct navigation.

    Reuses MultiseekResults verbatim — only the template differs.
    """
    return MultiseekResults.as_view(
        registry=settings.MULTISEEK_REGISTRY,
        template_name="htmx_fragments/results_fragment.html",
    )(request)
