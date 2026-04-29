from django import template

from core.pagination import build_compact_page_range

register = template.Library()


@register.filter
def compact_page_range(page_obj):
    return build_compact_page_range(page_obj)
