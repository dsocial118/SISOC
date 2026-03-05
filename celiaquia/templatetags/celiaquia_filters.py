# custom_filters.py
from django import template
from core.permissions.registry import resolve_permission_codes
from iam.services import user_has_permission_code

register = template.Library()


@register.filter(name="has_perm_code")
def has_perm_code(user, permission_alias):
    permission_codes = resolve_permission_codes([permission_alias])
    if not permission_codes:
        return False
    return any(user_has_permission_code(user, code) for code in permission_codes)
