from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context: dict[str, Any], **updates: Any) -> str:
    """
    Build a querystring based on current request.GET, with provided updates.

    - Pass `None` or "" to remove a key.
    - Pass an iterable (list/tuple/set) to set multiple values.
    """
    request = context.get("request")
    if request is None:
        q = QueryDict(mutable=True)
    else:
        q = request.GET.copy()

    for key, value in updates.items():
        if value is None or value == "":
            q.pop(key, None)
            continue

        if isinstance(value, Mapping):
            q[key] = str(value)
            continue

        if isinstance(value, (list, tuple, set)):
            q.setlist(key, [str(v) for v in value if v is not None and v != ""])
            continue

        # Any other scalar
        q[key] = str(value)

    return q.urlencode()