import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from centrodeinfancia.forms import CentroDeInfanciaForm
from centrodeinfancia.models import (
    CentroDeInfancia,
    DepartamentoIpi,
)
from core.models import Provincia
from users.models import Profile


@pytest.mark.django_db
def test_form_creacion_bloquea_provincia_si_usuario_tiene_provincia():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="user-provincia", password="test1234")

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()

    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Norte",
            "telefono": "1122334455",
            "telefono_referente": "1199887766",
        },
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is True
    assert form.fields["provincia"].initial == provincia
    assert form.is_valid() is True
    assert form.cleaned_data["provincia"] == provincia


@pytest.mark.django_db
def test_form_creacion_no_bloquea_provincia_si_usuario_no_tiene_provincia():
    user = User.objects.create_user(username="user-sin-provincia", password="test1234")

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = None
    profile.save()

    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Sur",
            "telefono": "1122334455",
            "telefono_referente": "1199887766",
        },
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is False
    assert form.is_valid() is True
    assert form.cleaned_data["provincia"] is None


@pytest.mark.django_db
def test_form_includes_apellido_referente_opcional():
    user = User.objects.create_user(username="user-apellido", password="test1234")
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Este",
            "apellido_referente": "Gómez",
            "telefono": "1122334455",
            "telefono_referente": "1199887766",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert "apellido_referente" in form.fields
    assert form.is_valid() is True
    assert form.cleaned_data["apellido_referente"] == "Gómez"


@pytest.mark.django_db
def test_form_acepta_numero_calle_opcional():
    user = User.objects.create_user(username="user-numero", password="test1234")
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Norte",
            "calle": "San Martín",
            "numero": "123",
            "telefono": "1122334455",
            "telefono_referente": "1199887766",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert "numero" in form.fields
    assert form.is_valid()
    assert form.cleaned_data["numero"] == "123"


@pytest.mark.django_db
def test_form_rechaza_texto_en_campos_numericos():
    user = User.objects.create_user(
        username="user-campos-numericos",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Texto",
            "numero": "12A",
            "telefono": "11-ABCD-1234",
            "telefono_referente": "abc",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    assert "numero" in form.errors
    assert "telefono" in form.errors
    assert "telefono_referente" in form.errors


@pytest.mark.django_db
def test_form_acepta_telefono_como_numero_plano():
    user = User.objects.create_user(
        username="user-telefono-plano",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Teléfono",
            "telefono": "5491140333588",
            "telefono_referente": "1133557799",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono"] == "5491140333588"
    assert form.cleaned_data["telefono_referente"] == "1133557799"


@pytest.mark.django_db
def test_form_acepta_telefono_con_guiones_opcionales():
    user = User.objects.create_user(
        username="user-telefono-guiones",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Teléfono Guiones",
            "telefono": "11-1234-1234",
            "telefono_referente": "549-11-4033-3588",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono"] == "11-1234-1234"
    assert form.cleaned_data["telefono_referente"] == "549-11-4033-3588"


@pytest.mark.django_db
def test_form_edicion_mantiene_campos_obligatorios():
    user = User.objects.create_user(
        username="user-edicion-obligatorios",
        password="test1234",
    )
    centro = CentroDeInfancia.objects.create(nombre="CDI Inicial")

    form = CentroDeInfanciaForm(
        data={"nombre": ""},
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    assert "nombre" in form.errors


@pytest.mark.django_db
def test_form_requiere_telefonos_en_creacion_y_edicion():
    user = User.objects.create_user(
        username="user-telefonos-obligatorios",
        password="test1234",
    )
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Teléfonos",
        telefono="1122334455",
        telefono_referente="1199887766",
    )

    form_creacion = CentroDeInfanciaForm(
        data={"nombre": "CDI Nuevo", "telefono": "", "telefono_referente": ""},
        user=user,
        lock_provincia_from_user=False,
    )
    form_edicion = CentroDeInfanciaForm(
        data={"nombre": centro.nombre, "telefono": "", "telefono_referente": ""},
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form_creacion.is_valid()
    assert form_creacion.errors["telefono"] == ["Este campo es obligatorio."]

    assert not form_edicion.is_valid()
    assert form_edicion.errors["telefono"] == ["Este campo es obligatorio."]
    assert "telefono_referente" not in form_edicion.errors


@pytest.mark.django_db
def test_edicion_centro_muestra_errores_si_se_eliminan_telefonos(client):
    user = User.objects.create_superuser(
        username="super-cdi-edicion-telefonos",
        email="super-cdi-edicion-telefonos@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Edicion",
        telefono="1122334455",
        telefono_referente="1199887766",
    )

    response = client.post(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro.pk}),
        {
            "nombre": centro.nombre,
            "telefono": "",
            "telefono_referente": "",
        },
    )

    assert response.status_code == 200
    assert response.context["form"].errors["telefono"] == ["Este campo es obligatorio."]
    assert "telefono_referente" not in response.context["form"].errors


@pytest.mark.django_db
def test_form_acepta_telefono_referente_vacio():
    user = User.objects.create_user(
        username="user-telefono-referente-opcional",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Referente Opcional",
            "telefono": "1122334455",
            "telefono_referente": "",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono_referente"] == ""


@pytest.mark.django_db
def test_form_guarda_horarios_y_normaliza_cuit():
    user = User.objects.create_user(
        username="user-cdi-horarios-cuit",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Horarios",
            "organizacion": "Asociacion Barrial",
            "cuit_organizacion_gestiona": "20-44535030-4",
            "telefono": "1122334455",
            "dias_funcionamiento": ["lunes", "martes"],
            "horario_lunes_apertura": "08:00",
            "horario_lunes_cierre": "12:00",
            "horario_martes_apertura": "08:00",
            "horario_martes_cierre": "12:00",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    centro = form.save()

    assert centro.cuit_organizacion_gestiona == "20445350304"
    assert list(
        centro.horarios_funcionamiento.order_by("dia").values_list(
            "dia", "hora_apertura", "hora_cierre"
        )
    ) == [
        (
            "lunes",
            form.cleaned_data["horario_lunes_apertura"],
            form.cleaned_data["horario_lunes_cierre"],
        ),
        (
            "martes",
            form.cleaned_data["horario_martes_apertura"],
            form.cleaned_data["horario_martes_cierre"],
        ),
    ]


@pytest.mark.django_db
def test_form_rechaza_horarios_para_dias_no_seleccionados():
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Horario Invalido",
            "telefono": "1122334455",
            "dias_funcionamiento": ["lunes"],
            "horario_martes_apertura": "08:00",
            "horario_martes_cierre": "12:00",
        }
    )

    assert not form.is_valid()
    assert "horario_martes_cierre" in form.errors


@pytest.mark.django_db
def test_form_filtra_departamentos_por_provincia():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    departamento_ba = DepartamentoIpi.objects.create(
        codigo_departamento="02001",
        provincia=provincia_ba,
        nombre="Comuna 1",
    )
    DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Norte", "provincia": provincia_ba.id}
    )

    departamento_ids = set(
        form.fields["departamento"].queryset.values_list("id", flat=True)
    )

    assert departamento_ids == {departamento_ba.id}


@pytest.mark.django_db
def test_form_rechaza_departamento_que_no_pertenece_a_la_provincia():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    departamento_sf = DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Invalido",
            "provincia": provincia_ba.id,
            "departamento": departamento_sf.id,
        }
    )

    assert not form.is_valid()
    assert "departamento" in form.errors


@pytest.mark.django_db
def test_form_muestra_decil_ipi_del_departamento_seleccionado():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    departamento = DepartamentoIpi.objects.create(
        codigo_departamento="02001",
        provincia=provincia,
        nombre="Comuna 1",
        decil_ipi=3,
    )
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Centro",
        provincia=provincia,
        departamento=departamento,
    )

    form = CentroDeInfanciaForm(instance=centro)

    assert "decil_ipi" in form.fields
    assert form.fields["decil_ipi"].disabled is True
    assert form.fields["decil_ipi"].initial == "3"


@pytest.mark.django_db
def test_form_bound_muestra_decil_ipi_del_departamento_en_post():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    departamento = DepartamentoIpi.objects.create(
        codigo_departamento="02001",
        provincia=provincia,
        nombre="Comuna 1",
        decil_ipi=7,
    )

    form = CentroDeInfanciaForm(
        data={
            "nombre": "",
            "provincia": provincia.id,
            "departamento": departamento.id,
        }
    )

    assert not form.is_valid()
    assert form.fields["decil_ipi"].initial == "7"
