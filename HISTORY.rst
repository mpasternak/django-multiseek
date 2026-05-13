0.10.0
------

Security & correctness:

* **CSRF protection enforced** on ``/results/`` and ``/save_form/``. Previously
  every multiseek URL was wrapped in ``csrf_exempt``. Downstream projects with
  custom templates must include ``{% csrf_token %}`` and surface the token to
  their JS layer. The bundled templates handle this automatically.
* **Concurrency race fixed** on the cached ``MultiseekRegistry``: parse errors
  no longer live on shared instance state. ``get_query()`` and
  ``get_query_for_model()`` accept an optional ``errors=`` list parameter.
  Backwards compatible for callers that ignore it.
* **XSS escape** in ``describe_multiseek_data()``: user-supplied ``prev_op``
  and ``operator`` are HTML-escaped before being inlined into the description
  rendered with ``|safe``. ``StringQueryObject.value_for_description`` now
  returns a ``SafeString``.
* **URL routing**: ``load_form/<pk>`` no longer accepts trailing path
  segments. All ``url()``/``re_path`` patterns migrated to ``path()`` with
  ``<int:>`` converters where applicable.
* **Manual-exclusion list-full** returns HTTP 400 (Bad Request) instead of
  403 (Forbidden).

Modernization:

* Drop Python 2 / six-era cruft (``from builtins import str as text`` and
  ``text(...)`` wrappers, ``class X(object):``, ``super(Cls, self)…``,
  ``u"..."`` prefixes, ``# -*- encoding: utf-8 -*-`` headers).
* Drop the ``mock`` third-party dependency in favour of stdlib
  ``unittest.mock``.
* Drop the dead ``django.db.models.options.get_verbose_name`` import shim
  (the fallback path has been the only live one since Django 1.9).
* Drop the dead ``if django.VERSION > (1, 8):`` template-context-processors
  branch in the demo project, plus the ``TEMPLATE_DEBUG``, ``sys.argv``
  middleware-stripping hack, and ``America/Chicago`` TIME_ZONE.

Tooling:

* Add ``ruff`` to dev deps; enable ``ruff check`` and ``ruff format --check``
  as hard gates in CI (no more ``|| true``).
* Format the codebase with ``ruff format``.
* Drop unused ``coveralls`` dev dep.

Public API:

* Re-export the public API from ``multiseek`` so you can
  ``from multiseek import create_registry, StringQueryObject, …`` directly.
* Add type hints to ``QueryObject``, ``MultiseekRegistry``, ``create_registry``,
  ``get_registry``, and the major subclass constructors.

Tests:

* Add regression tests for each of the substantive fixes above (race, CSRF,
  XSS, URL routing, list-full status code, public-API re-exports).

0.9.49
------

* Bump version after CI matrix touch-ups.

0.9.48
------

* Add safety margin for test_frame_bug teardown race condition.
* Add Django 6.0 to supported configurations (Python 3.12+ only).

0.9.47
------

* use GitHub Actions instead of Travis-CI
* Django 3.2 support,
* extract ordering and default queryset generation from ``get_query_for_model``,
  creating ``get_default_queryset_for_model`` and ``apply_ordering_to_queryset``.

0.9.46
------

* better date field handling when using with operators like greater, lesser, greater
  or equal, lesser or equal

0.9.45
------

* create a placeholder and an exception for form "parse errors"

0.9.44
------

* fix parameter passing in ``describe_multiseek_data``

0.9.43
------

* fix for DateQueryObject when there was range given
* fix for ``impacts_query`` parameters passing & test


0.9.32
------

* Foundation 6 as the only supported theme
