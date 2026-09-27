"""A tiny, self-contained icon system.

Every icon is a hand-authored 24x24 line glyph (1.75 stroke, round caps/joins)
so the whole app has one consistent icon language instead of emoji or a
mismatched grab-bag of one-off SVGs pasted per template.

Usage in a template:  {% load icons %}{% icon "trash" %}
"""
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

_WRAP = (
    '<svg class="icon {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
)

ICONS = {
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "calendar": (
        '<rect x="3" y="5" width="18" height="16" rx="2"/>'
        '<path d="M16 3v4M8 3v4M3 10h18"/>'
    ),
    "repeat": (
        '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
    ),
    "tag": (
        '<path d="M3 11.5V4a1 1 0 0 1 1-1h7.5a1 1 0 0 1 .7.3l8 8a1 1 0 0 1 0 1.4'
        'l-7.5 7.5a1 1 0 0 1-1.4 0l-8-8a1 1 0 0 1-.3-.7Z"/>'
        '<circle cx="7.5" cy="7.5" r="1.25"/>'
    ),
    "folder": '<path d="M3 7a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/>',
    "chart": '<path d="M4 20V10M12 20V4M20 20v-7"/><path d="M2 20h20"/>',
    "trash": (
        '<path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
        '<path d="M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"/>'
        '<path d="M10 11v6M14 11v6"/>'
    ),
    "edit": (
        '<path d="M12 20h9"/>'
        '<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>'
    ),
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "x-circle": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "logout": (
        '<path d="M9 21H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h4"/>'
        '<path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>'
    ),
    "login": (
        '<path d="M15 21h4a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-4"/>'
        '<path d="M8 7l-5 5 5 5"/><path d="M3 12h12"/>'
    ),
    "chevron-down": '<path d="M6 9l6 6 6-6"/>',
    "alert-triangle": (
        '<path d="M12 3.5 2.5 20h19L12 3.5Z"/><path d="M12 10v4"/><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none"/>'
    ),
    "inbox": (
        '<path d="M3 12h4.5l1.5 3h6l1.5-3H21"/>'
        '<path d="M5.5 5h13l2.5 7v7a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-7Z"/>'
    ),
    "rotate-ccw": (
        '<path d="M3 11V5l3 3"/>'
        '<path d="M3 8a9 9 0 1 1-2 6"/>'
    ),
    "user": '<circle cx="12" cy="8" r="3.5"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
    "layers": (
        '<path d="M12 3l9 5-9 5-9-5 9-5Z"/>'
        '<path d="M3 13l9 5 9-5"/>'
    ),
    "sub": '<path d="M6 3v10a3 3 0 0 0 3 3h9"/><path d="M14 12l4 4-4 4"/>',
}


@register.simple_tag
def icon(name, size=18, cls=""):
    body = ICONS.get(name, "")
    return mark_safe(_WRAP.format(size=size, body=body, cls=cls))
