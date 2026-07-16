"""Provisionamiento automático de usuarios vinculados al dominio CDI."""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from centrodeinfancia.models import AccesoCDI
from core.constants import UserGroups
from users.models import Profile
from users.services_generate_user import DatosUsuarioDelegado, generar_usuario_delegado
from users.territorial_scope import sync_profile_territorial_scopes


logger = logging.getLogger(__name__)
User = get_user_model()


def crear_referente_cdi_automaticamente(request, centro):
    """Crea el referente inicial sin comprometer el guardado del CDI."""
    datos_referente = {
        "first_name": (centro.nombre_referente or "").strip(),
        "last_name": (centro.apellido_referente or "").strip(),
        "email": (centro.email_referente or "").strip(),
    }
    if not datos_referente["email"]:
        messages.warning(
            request,
            "El CDI se guardó sin crear referente: falta el email del referente.",
        )
        return
    if not all(datos_referente.values()):
        messages.warning(
            request,
            "El CDI se guardó sin crear referente: complete nombre, apellido y email.",
        )
        return
    if AccesoCDI.objects.filter(centro=centro).exists():
        return
    if User.objects.filter(email__iexact=datos_referente["email"]).exists():
        logger.warning(
            "No se creó referente CDI porque el email ya está en uso centro_id=%s email=%s",
            centro.id,
            datos_referente["email"],
        )
        messages.warning(
            request,
            "El CDI se guardó sin crear referente: el email ya está asociado a un usuario.",
        )
        return

    try:
        resultado = generar_usuario_delegado(
            actor=request.user,
            datos=DatosUsuarioDelegado(**datos_referente),
            grupo_nombre=UserGroups.CDI_REFERENTE_CENTRO,
            vinculo_callback=lambda nuevo_usuario: AccesoCDI.objects.create(
                user=nuevo_usuario,
                centro=centro,
                creado_por=request.user,
            ),
            request=request,
        )
    except ValidationError as exc:
        logger.warning(
            "No se creó referente CDI automáticamente centro_id=%s actor_id=%s: %s",
            centro.id,
            request.user.id,
            "; ".join(exc.messages),
        )
        messages.warning(
            request,
            "El CDI se guardó, pero no se pudo crear el referente automáticamente.",
        )
    except Exception:  # noqa: BLE001 - el guardado primario no debe fallar
        logger.exception(
            "Error inesperado al crear referente CDI automáticamente centro_id=%s actor_id=%s",
            centro.id,
            request.user.id,
        )
        messages.warning(
            request,
            "El CDI se guardó, pero no se pudo crear el referente automáticamente.",
        )
    else:
        messages.success(
            request,
            f"Referente «{resultado['user'].username}» creado automáticamente.",
        )


def _vincular_usuario_trabajador(trabajador, user):
    trabajador.usuario = user
    trabajador.save(update_fields=["usuario"])


def crear_usuario_trabajador_automaticamente(request, trabajador):
    """Vincula un usuario al trabajador sin afectar el guardado de la nómina."""
    if trabajador.usuario_id or not (trabajador.email or "").strip():
        return
    if User.objects.filter(email__iexact=trabajador.email.strip()).exists():
        logger.warning(
            "No se creó usuario de trabajador porque el email ya está en uso trabajador_id=%s email=%s",
            trabajador.id,
            trabajador.email,
        )
        messages.warning(
            request,
            "El trabajador se guardó sin crear usuario: el email ya está asociado a un usuario.",
        )
        return

    try:
        resultado = generar_usuario_delegado(
            actor=request.user,
            datos=DatosUsuarioDelegado(
                first_name=trabajador.nombre,
                last_name=trabajador.apellido,
                email=trabajador.email,
            ),
            grupo_nombre=UserGroups.CDI_TRABAJADOR,
            vinculo_callback=lambda nuevo_usuario: _vincular_usuario_trabajador(
                trabajador,
                nuevo_usuario,
            ),
            request=request,
        )
    except ValidationError as exc:
        logger.warning(
            "No se creó usuario de trabajador automáticamente trabajador_id=%s actor_id=%s: %s",
            trabajador.id,
            request.user.id,
            "; ".join(exc.messages),
        )
        messages.warning(
            request,
            "El trabajador se guardó, pero no se pudo crear su usuario automáticamente.",
        )
    except Exception:  # noqa: BLE001 - el guardado primario no debe fallar
        logger.exception(
            "Error inesperado al crear usuario de trabajador trabajador_id=%s actor_id=%s",
            trabajador.id,
            request.user.id,
        )
        messages.warning(
            request,
            "El trabajador se guardó, pero no se pudo crear su usuario automáticamente.",
        )
    else:
        trabajador.usuario = resultado["user"]
        messages.success(
            request,
            f"Usuario de trabajador «{resultado['user'].username}» creado automáticamente.",
        )


def _sincronizar_email_si_cuenta_temporal(request, user, email, tipo_usuario):
    email = (email or "").strip()
    if not user or not email or user.email == email:
        return

    profile = getattr(user, "profile", None)
    if not getattr(profile, "must_change_password", False):
        messages.warning(
            request,
            f"No se actualizó el email del {tipo_usuario} porque ya modificó su cuenta.",
        )
        return

    user.email = email
    user.save(update_fields=["email"])
    messages.success(request, f"Email del {tipo_usuario} actualizado.")


def sincronizar_email_referente_cdi(request, centro, email_anterior):
    """Actualiza solo el acceso que corresponde al email anterior del referente."""
    accesos = AccesoCDI.objects.select_related("user", "user__profile").filter(
        centro=centro,
        activo=True,
    )
    candidatos = list(
        accesos.filter(user__email__iexact=(email_anterior or "").strip())[:2]
        if email_anterior
        else []
    )
    if not candidatos:
        candidatos = list(accesos.order_by("pk")[:2])
    acceso = candidatos[0] if len(candidatos) == 1 else None
    if acceso:
        _sincronizar_email_si_cuenta_temporal(
            request,
            acceso.user,
            centro.email_referente,
            "referente",
        )
    elif candidatos:
        logger.warning(
            "No se sincronizó email de referente por accesos ambiguos centro_id=%s",
            centro.id,
        )
        messages.warning(
            request,
            "No se actualizó el email del referente porque el CDI tiene múltiples accesos activos.",
        )


def sincronizar_email_trabajador(request, trabajador):
    _sincronizar_email_si_cuenta_temporal(
        request,
        trabajador.usuario,
        trabajador.email,
        "trabajador",
    )


def vincular_scope_provincial_egp(nuevo_usuario, provincia):
    """Marca un EGP como territorial y lo limita a una provincia completa."""
    profile, _ = Profile.objects.get_or_create(user=nuevo_usuario)
    profile.es_usuario_provincial = True
    profile.save(update_fields=["es_usuario_provincial"])
    sync_profile_territorial_scopes(
        profile,
        [
            {
                "provincia_id": provincia.id,
                "municipio_id": None,
                "localidad_id": None,
            }
        ],
    )
