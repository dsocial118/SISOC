from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from admisiones.models.admisiones import Admision
from comedores.models import (
    AuditComedorPrograma,
    Comedor,
    Nomina,
    Observacion,
    Referente,
)
from comedores.utils import comedor_usa_admision_para_nomina
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from comedores.tasks import (
    AsyncRemoveComedorToGestionar,
    AsyncSendComedorToGestionar,
    AsyncSendObservacionToGestionar,
    AsyncSendReferenteToGestionar,
    build_comedor_payload,
    build_observacion_payload,
    build_referente_payload,
)
from config.middlewares.threadlocals import get_current_user
from core.soft_delete.signals import post_restore, post_soft_delete
from relevamientos.models import Relevamiento
from rendicioncuentasfinal.models import (
    DocumentoRendicionFinal,
    RendicionCuentasFinal,
    TipoDocumentoRendicionFinal,
)
from users.api import aplicar_cambio_organizacion_comedor


def _current_user_id():
    current_user = get_current_user()
    return (
        current_user.pk
        if getattr(current_user, "is_authenticated", False)
        else None
    )


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_comedor_payload(instance)  # usa los NEW values de la instancia
        transaction.on_commit(
            lambda: AsyncSendComedorToGestionar(payload).start(),
            using=kwargs.get("using") or instance._state.db,
        )


@receiver(pre_save, sender=Comedor)
def update_comedor_in_gestionar(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = sender.objects.get(pk=instance.pk)

    programa_changed = previous.programa_id != instance.programa_id
    if programa_changed:
        previous_programa_id = previous.programa_id
        new_programa_id = instance.programa_id
        current_user = get_current_user()
        current_user_id = getattr(current_user, "pk", None)

        transaction.on_commit(
            lambda: AuditComedorPrograma.objects.create(
                comedor=instance,
                from_programa_id=previous_programa_id,
                to_programa_id=new_programa_id,
                changed_by_id=current_user_id,
            )
        )

    changed = any(
        f.name not in {"foto_legajo"}
        and getattr(instance, f.name) != getattr(previous, f.name)
        for f in instance._meta.fields
    )
    if not changed:
        return

    payload = build_comedor_payload(
        instance, action="Update"
    )  # usa los NEW values de la instancia
    transaction.on_commit(
        lambda: AsyncSendComedorToGestionar(payload).start(),
        using=kwargs.get("using") or instance._state.db,
    )


@receiver(pre_save, sender=Comedor)
def track_organizacion_anterior(sender, instance, **kwargs):
    """Guarda la organización previa para propagar el cambio a los accesos PWA."""
    database_alias = kwargs.get("using") or instance._state.db
    organizacion_anterior_id = (
        sender.all_objects.using(database_alias)
        .select_for_update()
        .filter(pk=instance.pk)
        .values_list("organizacion_id", flat=True)
        .first()
        if instance.pk
        else None
    )
    instance._pwa_organizacion_anterior_id = (  # pylint: disable=protected-access
        organizacion_anterior_id
    )


@receiver(post_save, sender=Comedor)
def sync_accesos_pwa_por_organizacion(sender, instance, created, **kwargs):
    """Mantiene los accesos PWA por organización al alta y al cambio de comedor.

    Los usuarios mobile asociados a una organización deben ver todos sus
    comedores sin intervención manual del administrador.
    """
    organizacion_anterior_id = (
        None if created else getattr(instance, "_pwa_organizacion_anterior_id", None)
    )
    if organizacion_anterior_id == instance.organizacion_id:
        return

    aplicar_cambio_organizacion_comedor(
        comedor_id=instance.pk,
        previous_organizacion_id=organizacion_anterior_id,
        new_organizacion_id=instance.organizacion_id,
        actor_id=_current_user_id(),
    )
    instance._pwa_organizacion_anterior_id = (  # pylint: disable=protected-access
        instance.organizacion_id
    )


@receiver(post_soft_delete, sender=Comedor)
def deactivate_accesos_pwa_por_soft_delete(sender, instance, user=None, **kwargs):
    """Revoca la proyección de un comedor eliminado lógicamente."""
    del sender, kwargs
    aplicar_cambio_organizacion_comedor(
        comedor_id=instance.pk,
        previous_organizacion_id=instance.organizacion_id,
        new_organizacion_id=None,
        actor_id=getattr(user, "pk", None),
    )


@receiver(post_restore, sender=Comedor)
def reactivate_accesos_pwa_por_restore(sender, instance, user=None, **kwargs):
    """Reconstruye la proyección al restaurar un comedor."""
    del sender, kwargs
    aplicar_cambio_organizacion_comedor(
        comedor_id=instance.pk,
        previous_organizacion_id=None,
        new_organizacion_id=instance.organizacion_id,
        actor_id=getattr(user, "pk", None),
    )


@receiver(pre_delete, sender=Comedor)
@receiver(post_soft_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, **kwargs):
    transaction.on_commit(
        lambda comedor_id=instance.id: AsyncRemoveComedorToGestionar(
            comedor_id
        ).start(),
        using=kwargs.get("using") or instance._state.db,
    )


@receiver(post_save, sender=Observacion)
def send_observacion_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_observacion_payload(instance)
        AsyncSendObservacionToGestionar(instance.id, payload).start()


@receiver(post_save, sender=Referente)
def send_referente_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_referente_payload(instance)
        AsyncSendReferenteToGestionar(instance.id, payload).start()


@receiver(post_save, sender=RendicionCuentasFinal)
def crear_documentos_por_defecto(sender, instance, created, **kwargs):
    if created:
        for tipo in TipoDocumentoRendicionFinal.objects.filter(personalizado=False):
            DocumentoRendicionFinal.objects.create(rendicion_final=instance, tipo=tipo)


@receiver(post_save, sender=Relevamiento)
def clasificacion_relevamiento(sender, instance, **kwargs):
    ClasificacionComedorService.create_clasificacion_relevamiento(instance)


@receiver(post_save, sender=Admision)
def asignar_nominas_directas_a_admision(sender, instance, created, **kwargs):
    """
    Al crear una admisión para comedores que usan ese flujo, reasigna las
    nóminas directas al nuevo convenio.

    Los programas con nómina directa nunca pasan por este camino; el helper
    centralizado evita que una admisión accidental reconfigure su nómina.
    """
    if not created:
        return
    comedor = instance.comedor
    if not comedor or not comedor_usa_admision_para_nomina(comedor):
        return
    Nomina.objects.filter(
        comedor=comedor,
        admision__isnull=True,
    ).update(admision=instance, comedor=None)
