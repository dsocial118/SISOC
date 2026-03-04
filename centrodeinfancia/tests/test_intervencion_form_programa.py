import pytest

from centrodeinfancia.forms import IntervencionCentroInfanciaForm
from intervenciones.forms import IntervencionForm, build_programa_aliases
from intervenciones.models.intervenciones import TipoIntervencion


@pytest.mark.django_db
def test_intervencion_form_comedores_filtra_tipos_por_programa_y_globales():
    tipo_global = TipoIntervencion.objects.create(nombre="Global")
    tipo_comedores = TipoIntervencion.objects.create(
        nombre="Solo Comedores",
        programa="comedores",
    )
    TipoIntervencion.objects.create(
        nombre="Solo Centro de Infancia",
        programa="cdi",
    )

    form = IntervencionForm()
    queryset_ids = set(
        form.fields["tipo_intervencion"].queryset.values_list("id", flat=True)
    )

    assert tipo_global.id in queryset_ids
    assert tipo_comedores.id in queryset_ids
    assert all(
        programa != "cdi"
        for programa in TipoIntervencion.objects.filter(
            id__in=queryset_ids
        ).values_list("programa", flat=True)
        if programa
    )


@pytest.mark.django_db
def test_intervencion_form_centro_infancia_filtra_tipos_por_programa_y_globales():
    tipo_global = TipoIntervencion.objects.create(nombre="Global")
    tipo_cdi = TipoIntervencion.objects.create(
        nombre="Solo Centro de Infancia",
        programa="cdi",
    )
    TipoIntervencion.objects.create(
        nombre="Solo Comedores",
        programa="comedores",
    )

    form = IntervencionCentroInfanciaForm()
    queryset_ids = set(
        form.fields["tipo_intervencion"].queryset.values_list("id", flat=True)
    )

    assert tipo_global.id in queryset_ids
    assert tipo_cdi.id in queryset_ids
    assert "comedores" not in set(
        (programa or "").lower()
        for programa in TipoIntervencion.objects.filter(
            id__in=queryset_ids
        ).values_list("programa", flat=True)
    )


@pytest.mark.django_db
def test_intervencion_form_comedor_custom_aliases_agrega_tipos_de_programa():
    tipo_global = TipoIntervencion.objects.create(nombre="Global")
    tipo_pac = TipoIntervencion.objects.create(nombre="Solo PAC", programa="PAC")
    TipoIntervencion.objects.create(
        nombre="Solo Centro de Infancia",
        programa="cdi",
    )

    form = IntervencionForm(programa_aliases=build_programa_aliases("PAC"))
    queryset_ids = set(
        form.fields["tipo_intervencion"].queryset.values_list("id", flat=True)
    )

    assert tipo_global.id in queryset_ids
    assert tipo_pac.id in queryset_ids
    assert all(
        programa.lower() != "cdi"
        for programa in TipoIntervencion.objects.filter(
            id__in=queryset_ids
        ).values_list("programa", flat=True)
        if programa
    )
