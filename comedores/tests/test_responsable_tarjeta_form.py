import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from core.models import Localidad, Municipio, Provincia
from comedores.forms.comedor_form import ResponsableTarjetaComedorForm
from comedores.models import Comedor, Programas


@pytest.mark.django_db
def test_responsable_tarjeta_filtra_localidades_por_provincia_y_persiste_carga_parcial():
    provincia = Provincia.objects.create(nombre="Provincia responsable")
    otra_provincia = Provincia.objects.create(nombre="Otra provincia")
    municipio = Municipio.objects.create(
        nombre="Municipio responsable", provincia=provincia
    )
    otro_municipio = Municipio.objects.create(
        nombre="Otro municipio", provincia=otra_provincia
    )
    localidad = Localidad.objects.create(
        nombre="Localidad responsable", municipio=municipio
    )
    localidad_ajena = Localidad.objects.create(
        nombre="Localidad ajena", municipio=otro_municipio
    )
    comedor = Comedor.objects.create(nombre="Comedor responsable")

    form = ResponsableTarjetaComedorForm(
        data={
            "responsable_tarjeta_nombre": "Responsable parcial",
            "responsable_tarjeta_provincia": provincia.pk,
            "responsable_tarjeta_localidad": localidad.pk,
        },
        instance=comedor,
    )

    assert form.is_valid()
    guardado = form.save()
    assert guardado.responsable_tarjeta_nombre == "Responsable parcial"
    assert guardado.responsable_tarjeta_localidad_id == localidad.pk
    assert list(form.fields["responsable_tarjeta_localidad"].queryset) == [localidad]

    form_invalido = ResponsableTarjetaComedorForm(
        data={
            "responsable_tarjeta_provincia": provincia.pk,
            "responsable_tarjeta_localidad": localidad_ajena.pk,
        },
        instance=comedor,
    )

    assert not form_invalido.is_valid()
    assert "responsable_tarjeta_localidad" in form_invalido.errors


@pytest.mark.django_db
def test_detalle_muestra_resumen_de_responsable_tarjeta_para_tecnico_comedor(
    client, comedor_fixture, django_user_model
):
    tecnico = django_user_model.objects.create_user(
        username="tecnico_responsable_tarjeta",
        email="tecnico-responsable@example.com",
        password="testpass",
    )
    tecnico.groups.add(Group.objects.get_or_create(name="Tecnico Comedor")[0])
    programa = Programas.objects.create(nombre="Alimentar comunidad")
    provincia = Provincia.objects.create(nombre="Provincia resumen")
    municipio = Municipio.objects.create(
        nombre="Municipio resumen", provincia=provincia
    )
    localidad = Localidad.objects.create(
        nombre="Localidad resumen", municipio=municipio
    )
    comedor_fixture.programa = programa
    comedor_fixture.responsable_tarjeta_nombre = "Responsable de resumen"
    comedor_fixture.responsable_tarjeta_dni = "40123456"
    comedor_fixture.responsable_tarjeta_cuit = "20-40123456-7"
    comedor_fixture.responsable_tarjeta_domicilio = "Calle de prueba 2403"
    comedor_fixture.responsable_tarjeta_localidad = localidad
    comedor_fixture.responsable_tarjeta_provincia = provincia
    comedor_fixture.responsable_tarjeta_telefono = "1100002403"
    comedor_fixture.save(
        update_fields=[
            "programa",
            "responsable_tarjeta_nombre",
            "responsable_tarjeta_dni",
            "responsable_tarjeta_cuit",
            "responsable_tarjeta_domicilio",
            "responsable_tarjeta_localidad",
            "responsable_tarjeta_provincia",
            "responsable_tarjeta_telefono",
        ]
    )
    client.force_login(tecnico)

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor_fixture.pk}))

    assert response.status_code == 200
    assert response.context["comedor"].pk == comedor_fixture.pk
    assert response.context["comedor"].programa.nombre == "Alimentar comunidad"
    assert response.context["puede_gestionar_responsable_tarjeta"] is True
    content = response.content.decode()
    assert "Responsable de la tarjeta" in content
    assert "Responsable de resumen" in content
    assert "40123456" in content
    assert "Localidad resumen" in content
    assert (
        reverse("comedor_responsable_tarjeta_editar", kwargs={"pk": comedor_fixture.pk})
        in content
    )
