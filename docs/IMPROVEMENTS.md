# Package review — most important improvements

This is a structured review of `django-multiseek` capturing the most impactful
improvements, ranked by impact. Companion to the freeform `PLAN` notes at the
repo root.

## 1. Concurrency bug: `MultiseekRegistry.errors` is shared state on a cached singleton

`multiseek/logic.py:715`:

```python
def get_query(self, data):
    self.errors = []
    return self.get_query_recursive(data)
```

But `MultiseekRegistry` is module-cached in `_cached_registry`
(`logic.py:920`) and `get_registry()` returns the *same instance* across every
request. Under a threaded gunicorn/uWSGI worker, two simultaneous searches
will stomp each other's `self.errors` list — and the view at `views.py:309`
reads `registry.errors` after `get_queryset()` to render error messages.

**Fix:** return errors out of `get_query()` instead of stashing on `self`. Or,
at minimum, document that the registry is not thread-safe and tell users to
deploy with `prefork` only. This is the only correctness bug I'd call urgent.

> This is the most common shape of a "works in dev / mysteriously wrong in
> prod" bug for Django middleware-style singletons: state that *feels*
> per-request (because it's overwritten at the start of every call) but
> actually lives on a shared object. It only manifests under concurrency.

## 2. CSRF disabled on all endpoints, including the form-save POST

`multiseek/urls.py:22,28,34,39` — every view is wrapped in `csrf_exempt`. The
save endpoint is gated by `user.is_staff`, but that's *exactly* the user a
CSRF attacker most wants to ride: a staff session is enough to overwrite any
saved search. The results POST writes user-supplied JSON into the session —
also a CSRF target (e.g. force a victim to commit to a specific filtered view
that hides results).

**Fix:** drop the blanket `csrf_exempt`. If something legitimately needs to be
CSRF-exempt, do it on that view only with a justification comment.

## 3. Python 2 / six-era cruft throughout

The package is `>=3.10`, but the source is full of:

- `from builtins import str as text` and `text(...)` wrappers —
  `multiseek/logic.py`, `views.py`, `util.py`, both test trees. All
  redundant; `str` works.
- `# -*- encoding: utf-8 -*-` at the top of every file — irrelevant since
  Py3.
- `class QueryObject(object):` (`logic.py:141`) — explicit `object`
  inheritance is noise.
- `super(StringQueryObject, self).…` (`logic.py:273`, `logic.py:306`,
  `logic.py:502`) — use `super()`.
- `u"%s"` / `u";\n".join(...)` literals (`logic.py:276`, `logic.py:892`,
  `models.py:17,30`) — drop the `u` prefix.
- `try: from django.db.models.options import get_verbose_name except
  ImportError: …` (`logic.py:16-19`) — that import was removed in Django
  1.9. The fallback is the only path on any supported Django.
- `try: from django.conf.urls import url except ImportError: from
  django.urls import re_path as url` (`urls.py:3-6`) — `re_path` is the only
  option since Django 4.0. Switch to `path()` while you're there.
- `from mock import MagicMock` (`tests/test_logic.py:10`) — use
  `unittest.mock`, then drop `mock` from
  `[project.optional-dependencies].dev`.
- `dict([(text(x.label), [text(x) for x in f.ops]) for f in fields])`
  patterns (`views.py:74`) — dict-comp is cleaner: `{str(f.label): [str(x)
  for x in f.ops] for f in fields}`.

There's a `python2-cleanup` skill that does this category-by-category. It's a
multi-commit cleanup, but it'd cut the cognitive load of every file
noticeably.

## 4. XSS risk in `describe_multiseek_data()` and `recreate_form()`

`views.py:278-282`:

```python
ret += "%s %s %s" % (
    d[cur]["field"].lower(),
    d[cur]["operator"],
    value,
)
```

The `field` and `operator` strings come from the user-supplied JSON. They're
matched against `registry.get_field_by_name()` before reaching this code, but
if `parse_field` doesn't strictly enforce the operator string to *be* one of
the canonical translations (the comparison goes through `[text(x) for x in
f.ops]` — these can include HTML if a translator ever inserts something), they
end up raw-inserted into the template via the `description` context variable.
Audit whether the template marks `description` as `|safe` — if so, this needs
`django.utils.html.format_html` / `escape`.

`recreate_form()` is worse: it builds a string of JavaScript by `%` formatting
and ships it into a `<script>` block. Field labels (developer-controlled) are
formatted in unescaped. If you ever allow user-defined field labels, you have
script injection.

**Fix:** escape `field`/`operator` in `describe_multiseek_data` with
`format_html`. For `recreate_form`, prefer rendering the form state as a JSON
blob inside a `<script type="application/json">` tag and parsing it in JS,
instead of generating JS at all.

## 5. Frontend is on dormant tech (Foundation 6 + jQuery)

This is the slowest-burning but biggest existential risk for the project.
Foundation 6's last release was 2022; jQuery is in legacy mode. `multiseek.js`
is 26 KB of hand-written jQuery widgets that nobody is going to learn
voluntarily. New Django projects in 2026 do not use either.

**Options, by ambition:**

- **Minimum:** vendor the Foundation 6 CSS you actually use and drop the yarn
  dependency from the test loop (currently CI installs yarn just to fetch
  Foundation 6 + jQuery for `collectstatic` — see
  `.github/workflows/tests.yml:42-46`).
- **Medium:** keep the JSON wire format, rewrite the frontend as a small
  Alpine.js or htmx + vanilla-JS UI. The DSL is well-isolated — the rewrite
  would not touch `logic.py`.
- **Maximal:** ship a headless mode (server-rendered or DRF-serialized) and
  let downstream projects render the UI however they want. The README already
  hints at this with the `django-ql` PLAN note.

## 6. CI silently swallows lint failures

`.github/workflows/tests.yml:74,77`:

```yaml
- name: Lint with ruff
  run: uv run ruff check . || true
- name: Check formatting with ruff
  run: uv run ruff format --check . || true
```

`|| true` means the lint job never fails. Either fix the existing violations
and drop `|| true`, or remove the lint job — the current state is the worst
of both worlds (looks green, signals nothing).

## 7. Stale demo settings

`test_project/test_project/settings.py`:

- `TEMPLATE_DEBUG = DEBUG` (line 7) — removed in Django 1.10.
- `'django.core.context_processors.*'` (lines 93-97) — moved to
  `django.template.context_processors.*` in Django 1.8. The code falls into
  the `if django.VERSION > (1,8):` block on any supported Django, so the
  first block is dead code that nobody can reach.
- `SITE_ID = 1` with no `django.contrib.sites` in `INSTALLED_APPS` —
  harmless but misleading.
- The `if 'test' in sys.argv: MIDDLEWARE = MIDDLEWARE[:-1]` hack (line 121) —
  `sys.argv[0]` under pytest is `pytest`, not `manage.py test`, so this
  branch never fires. If you actually need `LocaleMiddleware` off during
  tests, do it with a pytest fixture or a dedicated `test_settings.py`.

## 8. URL routing nit: missing `$` anchor

`multiseek/urls.py:54`:

```python
url(r'^load_form/(?P<search_form_pk>\d+)', load_form, name="load_form")
```

No trailing `$`, so `/load_form/123/anything` matches. Add it for consistency
with the other patterns. While you're refactoring `urls.py`, swap to
`path("load_form/<int:search_form_pk>/", …)`.

## 9. Public API has zero type hints

`QueryObject`, `MultiseekRegistry`, and `create_registry` are what downstream
users subclass and call. Even a minimal pass — annotating the constructor
signatures and the return types of `value_from_web`, `real_query`,
`query_for_model`, `add_field`, `get_query` — would dramatically improve
discoverability under any modern IDE.

## 10. Smaller items worth a single sweep

- **`HISTORY.rst` is stale** — last entry is 0.9.47, current version is
  0.9.49. Either keep the changelog current or drop the file.
- **`PLAN` file** at repo root looks like personal notes — keep separate
  from this structured review (its current role).
- **`SearchForm.data` is `TextField` holding JSON** (`models.py:24`) —
  Django 4.2+ supports `JSONField` portably across SQLite, Postgres, MySQL.
  Switch for proper type & indexability.
- **`MULTISEEK_SESSION_KEY_REMOVED` is capped at 2048** (`views.py:329`)
  but `HttpResponseForbidden` is a confusing response for "list full" —
  `HttpResponseBadRequest` or a 429 fits better.
- **`coveralls` is in dev deps** but no workflow step uploads coverage.
  Either wire it up or drop it.
- **`from django.utils.translation import gettext_lazy` is imported twice**
  in `views.py:12-13` (once as itself, once as `_`). Drop one.
- **`__init__.py` is empty** — fine, but expose the public API
  (`create_registry`, `QueryObject`, the subclasses, the operator
  constants) here so users can `from multiseek import create_registry,
  StringQueryObject` rather than reaching into `multiseek.logic`.

## Suggested order of attack

If you want a low-risk incremental path:

1. **Items 1, 2, 6, 8** — single-PR safety/security fixes. Small diffs,
   immediate value.
2. **Item 3** — Python 2 cleanup via the dedicated skill. Mechanical, big
   readability gain, separate commits per category.
3. **Item 7 + 10** — settings/demos hygiene.
4. **Item 9** — type hints on public surface.
5. **Item 4** — XSS audit; needs template inspection that was not done in
   this pass.
6. **Item 5** — the frontend rewrite is the big one. Worth its own design
   doc.

Items 1, 2, 4, 5 are the ones to treat as "really should fix this." The rest
is technical-debt cleanup that becomes easier once those are done.
