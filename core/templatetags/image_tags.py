"""Template tags para imágenes optimizadas con WebP."""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import logging

from core.services.image_service import get_or_create_webp

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def optimized_image(
    image_field,
    alt_text="",
    css_class="",
    loading="lazy",
    width=None,
    height=None,
    extra_attrs="",
):
    """
    Renderiza imagen optimizada con WebP y fallback.
    Genera <picture> con lazy loading por defecto.
    """
    if not image_field:
        return ""

    try:
        if hasattr(image_field, "url"):
            original_url = image_field.url
        else:
            original_url = str(image_field)

        if not original_url:
            return ""

        webp_url = get_or_create_webp(original_url)

        img_attrs = []

        if css_class:
            img_attrs.append(f'class="{css_class}"')

        if loading in ("lazy", "eager"):
            img_attrs.append(f'loading="{loading}"')

        if width:
            img_attrs.append(f'width="{width}"')

        if height:
            img_attrs.append(f'height="{height}"')

        if extra_attrs:
            img_attrs.append(extra_attrs)

        attrs_string = mark_safe(" " + " ".join(img_attrs)) if img_attrs else ""

        if webp_url != original_url and webp_url.endswith(".webp"):
            html = format_html(
                "<picture>"
                '<source srcset="{}" type="image/webp">'
                '<img src="{}" alt="{}"{}>'
                "</picture>",
                webp_url,
                original_url,
                alt_text,
                attrs_string,
            )
        else:
            html = format_html(
                '<img src="{}" alt="{}"{}>',
                original_url,
                alt_text,
                attrs_string,
            )

        return html

    except Exception as e:
        logger.error(f"Error en optimized_image: {e}", exc_info=True)

        try:
            if hasattr(image_field, "url"):
                return format_html(
                    '<img src="{}" alt="{}" class="{}">',
                    image_field.url,
                    alt_text,
                    css_class,
                )
        except Exception:
            pass

        return ""


@register.simple_tag
def webp_exists(image_field):
    """Verifica si existe la versión WebP de una imagen."""
    if not image_field:
        return False

    try:
        from core.services.image_service import _get_absolute_path, _get_webp_path
        import os

        if hasattr(image_field, "url"):
            image_path = image_field.url
        else:
            image_path = str(image_field)

        abs_path = _get_absolute_path(image_path)
        webp_path = _get_webp_path(abs_path)

        return os.path.exists(webp_path)

    except Exception as e:
        logger.error(f"Error en webp_exists: {e}")
        return False


@register.filter
def webp_url(image_field):
    """Filtro para obtener la URL del WebP sin renderizar HTML."""
    if not image_field:
        return ""

    try:
        if hasattr(image_field, "url"):
            original_url = image_field.url
        else:
            original_url = str(image_field)

        return get_or_create_webp(original_url)

    except Exception as e:
        logger.error(f"Error en webp_url: {e}")
        if hasattr(image_field, "url"):
            return image_field.url
        return str(image_field) if image_field else ""


@register.simple_tag
def picture_tag(image_field, alt_text="", **kwargs):
    """Alias de optimized_image."""
    return optimized_image(image_field, alt_text, **kwargs)


@register.simple_tag
def image_info(image_field):
    """Obtiene información detallada de una imagen para debugging."""
    from core.services.image_service import get_image_info

    if not image_field:
        return None

    try:
        if hasattr(image_field, "url"):
            return get_image_info(image_field.url)
        else:
            return get_image_info(str(image_field))
    except Exception as e:
        logger.error(f"Error en image_info: {e}")
        return None
