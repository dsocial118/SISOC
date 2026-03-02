"""Regresión: tests para soft delete en ArchivoAdmision.

Valida que el cambio de QuerySet behavior con SoftDeleteManager no rompa:
- Queries existentes de listado de archivos
- Relaciones reverse desde Admision
- Filtros combinados
"""

import pytest
from django.contrib.auth import get_user_model

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    EstadoAdmision,
    Documentacion,
)
from comedores.models import Comedor


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def user_fixture():
    return User.objects.create_user(
        username="test_soft_delete_user",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def comedor_fixture():
    return Comedor.objects.create(nombre="Comedor Test Soft Delete")


@pytest.fixture
def estado_fixture():
    return EstadoAdmision.objects.create(nombre="Pendiente")


@pytest.fixture
def documentacion_fixture():
    return Documentacion.objects.create(
        nombre="DNI",
        obligatorio=True,
    )


@pytest.fixture
def admision_fixture(user_fixture, estado_fixture, comedor_fixture):
    return Admision.objects.create(
        comedor=comedor_fixture,
        estado=estado_fixture,
        usuario_provincia=user_fixture,
    )


def test_archivo_admision_soft_deleted_excluido_de_queries_normales(
    admision_fixture, user_fixture, documentacion_fixture
):
    """
    Regresión: ArchivoAdmision.objects.all() excluye soft-deleted.

    Valida que después de soft delete, la query normal no retorna el archivo
    (pero all_objects sí lo incluye).
    """
    # Crear archivo
    archivo = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
        observaciones="Test archivo",
    )
    archivo_pk = archivo.pk

    # Verificar que está en query normal
    assert ArchivoAdmision.objects.filter(admision=admision_fixture).count() == 1
    assert ArchivoAdmision.objects.filter(
        pk=archivo_pk
    ).exists(), "Archivo debe existir antes de delete"

    # Soft delete
    archivo.delete(user=user_fixture)

    # Verificar que NOW está excluido de query normal
    assert (
        ArchivoAdmision.objects.filter(admision=admision_fixture).count() == 0
    ), "Soft deleted archivo debe estar excluido de queries normales"
    assert (
        ArchivoAdmision.objects.filter(pk=archivo_pk).exists() is False
    ), "Soft deleted archivo no debe existir en query normal"

    # Verificar que ESTÁ en all_objects (incluye soft-deleted)
    assert (
        ArchivoAdmision.all_objects.filter(admision=admision_fixture).count() == 1
    ), "Soft deleted archivo debe estar en all_objects"
    assert ArchivoAdmision.all_objects.filter(
        pk=archivo_pk
    ).exists(), "Soft deleted archivo debe existir en all_objects"

    # Verificar que deleted_at y deleted_by fueron seteados
    deleted_archivo = ArchivoAdmision.all_objects.get(pk=archivo_pk)
    assert deleted_archivo.deleted_at is not None, "deleted_at debe estar seteado"
    assert (
        deleted_archivo.deleted_by_id == user_fixture.id
    ), "deleted_by debe ser el usuario"


def test_archivo_admision_reverse_relation_respeta_soft_delete(
    admision_fixture, user_fixture, documentacion_fixture
):
    """
    Regresión: admision.archivoadmision_set respeta soft delete.

    Valida que `.archivoadmision_set.all()` excluye soft-deleted en queries reverse.
    """
    archivo = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
    )

    # Antes de soft delete
    assert admision_fixture.archivoadmision_set.count() == 1

    # Soft delete
    archivo.delete(user=user_fixture)

    # Después de soft delete: relación reverse excluye
    assert (
        admision_fixture.archivoadmision_set.count() == 0
    ), "Reverse relation debe excluir soft-deleted"

    # Pero all_objects sí lo ve
    assert ArchivoAdmision.all_objects.filter(admision=admision_fixture).count() == 1


def test_archivo_admision_multiple_soft_deleted(
    admision_fixture, user_fixture, documentacion_fixture
):
    """
    Regresión: múltiples archivos, algunos deleted.

    Verifica que un mix de normal + soft-deleted se filtre correctamente.
    """
    arch1 = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
        observaciones="Archivo 1",
    )
    arch2 = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
        observaciones="Archivo 2",
    )
    arch3 = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
        observaciones="Archivo 3",
    )

    # Soft delete archivo 2
    arch2.delete(user=user_fixture)

    # Query normal: solo arch1 y arch3
    normal_qs = list(
        ArchivoAdmision.objects.filter(admision=admision_fixture).values_list(
            "pk", flat=True
        )
    )
    assert set(normal_qs) == {arch1.pk, arch3.pk}

    # all_objects: todos los 3
    all_qs = list(
        ArchivoAdmision.all_objects.filter(admision=admision_fixture).values_list(
            "pk", flat=True
        )
    )
    assert set(all_qs) == {arch1.pk, arch2.pk, arch3.pk}


def test_archivo_admision_soft_delete_restore(
    admision_fixture, user_fixture, documentacion_fixture
):
    """
    Regresión: restore trae el archivo de vuelta.

    Valida que `.restore()` reactive un soft-deleted.
    """
    archivo = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
    )
    archivo_pk = archivo.pk

    # Soft delete
    archivo.delete(user=user_fixture)
    assert ArchivoAdmision.objects.filter(pk=archivo_pk).exists() is False

    # Restore
    deleted_archivo = ArchivoAdmision.all_objects.get(pk=archivo_pk)
    deleted_archivo.restore(user=user_fixture)

    # Ahora está de vuelta en query normal
    assert ArchivoAdmision.objects.filter(pk=archivo_pk).exists()
    assert (
        deleted_archivo.deleted_at is None
    ), "deleted_at debe ser None después de restore"


def test_archivo_admision_prefetch_related_respeta_soft_delete(
    admision_fixture, user_fixture, documentacion_fixture
):
    """
    Regresión: prefetch_related respeta soft delete managers.

    Valida que `prefetch_related("archivos")` no incluya soft-deleted.
    """
    archivo = ArchivoAdmision.objects.create(
        admision=admision_fixture,
        documentacion=documentacion_fixture,
    )

    # Con prefetch_related
    admision = Admision.objects.prefetch_related("archivoadmision_set").get(
        pk=admision_fixture.pk
    )
    assert admision.archivoadmision_set.count() == 1

    # Soft delete
    archivo.delete(user=user_fixture)

    # Refetch con prefetch
    admision = Admision.objects.prefetch_related("archivoadmision_set").get(
        pk=admision_fixture.pk
    )
    assert admision.archivoadmision_set.count() == 0
