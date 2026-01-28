from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter
def has_group(user, group_name):
    """Check if user belongs to a group."""
    return user.groups.filter(name=group_name).exists()


@register.filter
def format_yyyymm(value):
    """Format date as YYYYMM."""
    if not value:
        return ""
    try:
        return value.strftime("%Y%m")
    except (AttributeError, TypeError):
        return str(value)
