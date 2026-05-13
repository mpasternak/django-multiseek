"""URL patterns for the htmx_fragments app.

All endpoints are addressed by a dotted ``path`` (e.g. ``"0.2.1"``). The path
identifies a node inside the multiseek ``form_data`` tree stored in the user's
session:

* ``"0"``      -> the root frame.
* ``"0.N"``    -> the Nth element of the root frame.
* ``"0.N.M"``  -> the Mth element of the Nth sub-frame, and so on.

Paths are simple, stable as long as no element is added or removed at an
earlier index in the same level. Because every mutation returns a re-rendered
fragment, this is fine in practice.
"""
from django.urls import path

from htmx_fragments import views

app_name = "htmx_fragments"

urlpatterns = [
    path("add-field/<path:elpath>/", views.add_field, name="add_field"),
    path("add-frame/<path:elpath>/", views.add_frame, name="add_frame"),
    path("element/<path:elpath>/", views.delete_element, name="delete_element"),
    path("field-type/<path:elpath>/", views.change_field_type, name="change_field_type"),
    path("field-value/<path:elpath>/", views.set_field_value, name="set_field_value"),
    path("field-prev-op/<path:elpath>/", views.set_field_prev_op, name="set_field_prev_op"),
]
