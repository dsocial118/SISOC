"""Servicio de optimización de imágenes con WebP."""

import os
import logging
from pathlib import Path
from typing import Optional
from PIL import Image
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

WEBP_QUALITY = 85
WEBP_CACHE_TIMEOUT = 3600
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def get_or_create_webp(image_path: str, quality: int = WEBP_QUALITY) -> str:
    """
    Obtiene o genera la versión WebP de una imagen.
    Retorna la ruta WebP si existe/se genera, o la original como fallback.
    """
    if not image_path:
        return ""

    file_ext = Path(image_path).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        return image_path

    try:
        original_abs_path = _get_absolute_path(image_path)

        if not os.path.exists(original_abs_path):
            logger.warning(f"Imagen original no encontrada: {original_abs_path}")
            return image_path

        webp_abs_path = _get_webp_path(original_abs_path)
        webp_relative_path = _get_webp_path(image_path)

        cache_key = f"webp_exists:{webp_abs_path}"
        if cache.get(cache_key):
            return webp_relative_path

        if os.path.exists(webp_abs_path):
            cache.set(cache_key, True, WEBP_CACHE_TIMEOUT)
            return webp_relative_path

        logger.info(f"Generando WebP para: {original_abs_path}")
        success = _convert_to_webp(original_abs_path, webp_abs_path, quality)

        if success:
            cache.set(cache_key, True, WEBP_CACHE_TIMEOUT)
            return webp_relative_path
        else:
            logger.warning(f"Fallo conversión WebP, usando original: {image_path}")
            return image_path

    except Exception as e:
        logger.error(f"Error en get_or_create_webp para {image_path}: {e}", exc_info=True)
        return image_path


def _convert_to_webp(input_path: str, output_path: str, quality: int) -> bool:
    """Convierte una imagen a formato WebP."""
    try:
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "LA"):
                pass
            elif img.mode == "P":
                img = img.convert("RGBA")
            elif img.mode == "L":
                img = img.convert("RGB")
            elif img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            img.save(
                output_path,
                format="WEBP",
                quality=quality,
                method=6,
                lossless=False,
            )

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                logger.error(f"Archivo WebP creado pero vacío: {output_path}")
                return False

    except Exception as e:
        logger.error(f"Error convirtiendo {input_path} a WebP: {e}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as cleanup_error:
                logger.error(f"Error limpiando archivo parcial: {cleanup_error}")
        return False


def _get_absolute_path(image_path: str) -> str:
    """Convierte ruta relativa o URL a ruta absoluta del sistema."""
    if os.path.isabs(image_path):
        return image_path

    if image_path.startswith(settings.MEDIA_URL):
        image_path = image_path[len(settings.MEDIA_URL) :]

    return os.path.join(settings.MEDIA_ROOT, image_path)


def _get_webp_path(image_path: str) -> str:
    """Genera la ruta WebP (misma carpeta, extensión .webp)."""
    return str(Path(image_path).with_suffix(".webp"))


def get_image_info(image_path: str) -> Optional[dict]:
    """Obtiene información detallada de una imagen para debugging."""
    try:
        abs_path = _get_absolute_path(image_path)

        if not os.path.exists(abs_path):
            return None

        with Image.open(abs_path) as img:
            info = {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "file_size": os.path.getsize(abs_path),
                "has_webp": os.path.exists(_get_webp_path(abs_path)),
            }

            if info["has_webp"]:
                webp_path = _get_webp_path(abs_path)
                info["webp_size"] = os.path.getsize(webp_path)
                info["savings_bytes"] = info["file_size"] - info["webp_size"]
                info["savings_percent"] = round(
                    (info["savings_bytes"] / info["file_size"]) * 100, 2
                )

            return info

    except Exception as e:
        logger.error(f"Error obteniendo info de {image_path}: {e}")
        return None


def clear_webp_cache(image_path: Optional[str] = None) -> None:
    """Limpia la caché de WebP."""
    if image_path:
        abs_path = _get_absolute_path(image_path)
        webp_path = _get_webp_path(abs_path)
        cache_key = f"webp_exists:{webp_path}"
        cache.delete(cache_key)
    else:
        cache.clear()
        logger.warning("Toda la caché de Django ha sido limpiada")
