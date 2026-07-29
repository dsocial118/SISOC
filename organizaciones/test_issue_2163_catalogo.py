"""Regresiones del catálogo de entidades para el issue #2163."""

from importlib import import_module

from organizaciones.forms import OrganizacionForm
from organizaciones.models import Organizacion, SubtipoEntidad, TipoEntidad


def test_formulario_omite_subtipos_inactivos_y_conserva_el_legado_en_edicion(db):
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    activo = SubtipoEntidad.objects.create(nombre="Asociación Civil", tipo_entidad=tipo)
    legado = SubtipoEntidad.objects.create(
        nombre="Entidad", tipo_entidad=tipo, activo=False
    )
    organizacion = Organizacion.objects.create(
        nombre="Organización histórica",
        tipo_entidad=tipo,
        subtipo_entidad=legado,
    )

    alta = OrganizacionForm()
    edicion = OrganizacionForm(instance=organizacion)

    assert list(alta.fields["subtipo_entidad"].queryset) == [activo]
    assert set(edicion.fields["subtipo_entidad"].queryset) == {activo, legado}


def test_migracion_unifica_obispado_y_preserva_entidad_historica(db):
    juridica = TipoEntidad.objects.create(nombre="Personería jurídica")
    eclesiastica = TipoEntidad.objects.create(nombre="Personería jurídica eclesiástica")
    obispado = SubtipoEntidad.objects.create(
        nombre="Obispado", tipo_entidad=eclesiastica
    )
    entidad = SubtipoEntidad.objects.create(nombre="Entidad", tipo_entidad=juridica)
    organizacion_obispado = Organizacion.objects.create(
        nombre="Diócesis histórica",
        tipo_entidad=eclesiastica,
        subtipo_entidad=obispado,
    )
    organizacion_entidad = Organizacion.objects.create(
        nombre="Entidad histórica",
        tipo_entidad=juridica,
        subtipo_entidad=entidad,
    )

    migration = import_module(
        "organizaciones.migrations.0017_issue_2163_catalogo_entidades"
    )
    migration.actualizar_catalogo(import_module("django.apps").apps, None)

    organizacion_obispado.refresh_from_db()
    organizacion_entidad.refresh_from_db()
    entidad.refresh_from_db()

    assert organizacion_obispado.subtipo_entidad.nombre == "Diócesis – Obispado"
    assert organizacion_entidad.subtipo_entidad_id == entidad.pk
    assert entidad.activo is False
    assert TipoEntidad.objects.filter(
        nombre="Simple Asociación (art. 187 CCCN)"
    ).exists()
