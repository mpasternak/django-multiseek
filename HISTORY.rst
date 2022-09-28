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
