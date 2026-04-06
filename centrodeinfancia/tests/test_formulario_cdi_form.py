import pytest
from django.contrib.auth.models import User

from centrodeinfancia.forms import FormularioCDIForm
from centrodeinfancia.formulario_cdi_schema import CAMPOS_OPCIONES, ETIQUETAS_CAMPOS
from centrodeinfancia.models import CentroDeInfancia, DepartamentoIpi, FormularioCDI
from core.models import Localidad, Municipio, Provincia


@pytest.mark.django_db
def test_formulario_cdi_requiere_texto_para_jornada_otra():
    centro = CentroDeInfancia.objects.create(nombre="CDI Norte")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "tipo_jornada": "other",
        }
    )

    assert not form.is_valid()
    assert "tipo_jornada_otra" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_no_permite_meals_ninguna_con_otras():
    centro = CentroDeInfancia.objects.create(nombre="CDI Sur")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "prestaciones_alimentarias": ["ninguna", "desayuno"],
        }
    )

    assert not form.is_valid()
    assert "prestaciones_alimentarias" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_form_acepta_payload_minimo():
    user = User.objects.create_user(username="formulario-minimo", password="test1234")
    centro = CentroDeInfancia.objects.create(nombre="CDI Este")
    form = FormularioCDIForm(
        data={
            "fecha_relevamiento": "2026-03-13",
            "nombre_completo_respondente": "Ana Perez",
            "rol_respondente": "Coordinacion",
            "email_respondente": "ana@example.com",
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    instance.centro = centro
    instance.created_by = user
    instance.save()

    assert instance.pk is not None


@pytest.mark.django_db
def test_formulario_cdi_acepta_telefonos_con_formato_flexible():
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Telefonos",
        telefono="12345678",
        telefono_referente="1122334455",
    )
    form = FormularioCDIForm(
        data={
            "fecha_relevamiento": "2026-03-13",
            "nombre_completo_respondente": "Ana Perez",
            "rol_respondente": "Coordinacion",
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "telefono_cdi": "12345678",
            "telefono_referente_cdi": "11-2233-4455",
            "telefono_organizacion": "22334455",
            "telefono_referente_organizacion": "54-11-99887766",
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono_cdi"] == "12345678"
    assert form.cleaned_data["telefono_referente_cdi"] == "11-2233-4455"


@pytest.mark.django_db
def test_formulario_cdi_normaliza_cuit_y_guarda_horarios_relacionados():
    centro = CentroDeInfancia.objects.create(nombre="CDI Horarios")
    formulario = FormularioCDI.objects.create(centro=centro, codigo_cdi="CDI-000001")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": formulario.codigo_cdi,
            "cuit_organizacion_gestora": "20-44535030-4",
            "dias_funcionamiento": ["lunes", "martes"],
            "horario_lunes_apertura": "08:00",
            "horario_lunes_cierre": "12:00",
            "horario_martes_apertura": "09:00",
            "horario_martes_cierre": "13:00",
            "source_form_version": 1,
        },
        instance=formulario,
    )

    assert form.is_valid(), form.errors
    saved = form.save()

    assert saved.cuit_organizacion_gestora == "20445350304"
    assert list(
        saved.horarios_funcionamiento.order_by("dia").values_list(
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
    assert saved.horario_apertura == form.cleaned_data["horario_lunes_apertura"]
    assert saved.horario_cierre == form.cleaned_data["horario_lunes_cierre"]


@pytest.mark.django_db
def test_formulario_cdi_rechaza_horarios_para_dias_no_seleccionados():
    centro = CentroDeInfancia.objects.create(nombre="CDI Horario Invalido")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": "CDI-000001",
            "dias_funcionamiento": ["lunes"],
            "horario_martes_apertura": "08:00",
            "horario_martes_cierre": "12:00",
            "source_form_version": 1,
        }
    )

    assert not form.is_valid()
    assert "horario_martes_cierre" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_rechaza_telefonos_con_caracteres_invalidos():
    centro = CentroDeInfancia.objects.create(nombre="CDI Telefono Invalido")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "telefono_cdi": "11-ABCD-1234",
            "telefono_referente_cdi": "abc",
            "source_form_version": 1,
        }
    )

    assert not form.is_valid()
    assert "telefono_cdi" in form.errors
    assert "telefono_referente_cdi" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_filtra_municipio_y_localidad_por_ubicacion_seleccionada():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    municipio_ba = Municipio.objects.create(nombre="La Plata", provincia=provincia_ba)
    Municipio.objects.create(nombre="Rosario", provincia=provincia_sf)
    localidad_ba = Localidad.objects.create(nombre="Tolosa", municipio=municipio_ba)
    Localidad.objects.create(
        nombre="Fisherton",
        municipio=Municipio.objects.get(nombre="Rosario"),
    )

    form = FormularioCDIForm(
        data={
            "provincia_cdi": provincia_ba.pk,
            "municipio_cdi": municipio_ba.pk,
            "localidad_cdi": localidad_ba.pk,
        }
    )

    municipio_ids = set(
        form.fields["municipio_cdi"].queryset.values_list("id", flat=True)
    )
    localidad_ids = set(
        form.fields["localidad_cdi"].queryset.values_list("id", flat=True)
    )

    assert municipio_ids == {municipio_ba.id}
    assert localidad_ids == {localidad_ba.id}


@pytest.mark.django_db
def test_formulario_cdi_filtra_departamentos_por_provincia():
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

    form = FormularioCDIForm(data={"provincia_cdi": provincia_ba.pk})

    departamento_ids = set(
        form.fields["departamento_cdi"].queryset.values_list("id", flat=True)
    )

    assert departamento_ids == {departamento_ba.id}


@pytest.mark.django_db
def test_formulario_cdi_rechaza_departamento_que_no_pertenece_a_la_provincia():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    departamento_sf = DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = FormularioCDIForm(
        data={
            "nombre_cdi": "CDI Invalido",
            "codigo_cdi": "CDI-000001",
            "provincia_cdi": provincia_ba.pk,
            "departamento_cdi": departamento_sf.pk,
            "source_form_version": 1,
        }
    )

    assert not form.is_valid()
    assert "departamento_cdi" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_rechaza_departamento_organizacion_invalido():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    departamento_sf = DepartamentoIpi.objects.create(
        codigo_departamento="82001",
        provincia=provincia_sf,
        nombre="Rosario",
    )

    form = FormularioCDIForm(
        data={
            "nombre_cdi": "CDI Invalido",
            "codigo_cdi": "CDI-000001",
            "provincia_organizacion": provincia_ba.pk,
            "departamento_organizacion": departamento_sf.pk,
            "source_form_version": 1,
        }
    )

    assert not form.is_valid()
    assert "departamento_organizacion" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_inicializa_departamento_desde_la_instancia():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    departamento = DepartamentoIpi.objects.create(
        codigo_departamento="02001",
        provincia=provincia,
        nombre="Comuna 1",
    )
    centro = CentroDeInfancia.objects.create(nombre="CDI Inicializacion")
    formulario = FormularioCDI.objects.create(
        centro=centro,
        provincia_cdi=provincia,
        departamento_cdi=departamento,
    )

    form = FormularioCDIForm(instance=formulario)

    assert form.fields["departamento_cdi"].initial == departamento


@pytest.mark.django_db
def test_formulario_cdi_labels_custom_quedan_en_espanol():
    form = FormularioCDIForm()

    assert (
        form.fields["meses_funcionamiento"].label == "Meses de funcionamiento del CDI"
    )
    assert form.fields["dias_funcionamiento"].label == "Días de funcionamiento del CDI"
    assert form.fields["tiene_extintores_vigentes"].label == "Existencia de extintores"
    assert form.fields["tiene_instrumento_priorizacion_ingreso"].label == (
        "Existe instrumento de priorización de ingreso de los niños/as"
    )


@pytest.mark.django_db
def test_formulario_cdi_limpia_valores_de_campos_ocultos_por_skip_logic():
    centro = CentroDeInfancia.objects.create(nombre="CDI Ocultos")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "tiene_espacio_cocina": "no",
            "combustible_cocinar": "gas_red",
            "tiene_espacio_exterior": "no",
            "tiene_juegos_exteriores": "si",
            "prestaciones_alimentarias": ["ninguna"],
            "calidad_elaboracion_menu": "sin_nutricionista_ultraprocesados",
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["combustible_cocinar"] == ""
    assert form.cleaned_data["tiene_juegos_exteriores"] == ""
    assert form.cleaned_data["calidad_elaboracion_menu"] == ""


@pytest.mark.django_db
def test_formulario_cdi_limpia_seguridad_electrica_si_no_tiene_electricidad():
    centro = CentroDeInfancia.objects.create(nombre="CDI Sin Electricidad")
    form = FormularioCDIForm(
        data={
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "acceso_energia": "sin_electricidad",
            "seguridad_electrica": "cumple_y_revision_anual",
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["seguridad_electrica"] == ""


@pytest.mark.django_db
def test_formulario_cdi_aplica_textos_actualizados_en_labels_y_opciones():
    form = FormularioCDIForm()

    assert form.fields["fecha_relevamiento"].label == "Fecha de Relevamiento"
    assert (
        form.fields["acceso_internet_personal"].label
        == "Acceso a internet: ¿El CDI tiene acceso a internet y es compartido por el personal?"
    )
    assert (
        dict(form.fields["acceso_agua"].choices)["caneria_dentro_cdi"]
        == "Por cañería dentro del CDI"
    )
    assert (
        dict(form.fields["acceso_internet_personal"].choices)[
            "estable_sin_acceso_personal"
        ]
        == "El CDI cuenta con un servicio de internet relativamente estable al que accede el personal"
    )


@pytest.mark.django_db
def test_formulario_cdi_opciones_botiquin_muestran_texto_largo():
    form = FormularioCDIForm()

    assert (
        dict(form.fields["estado_botiquin_primeros_auxilios"].choices)[
            "completo_todas_salas_ok_vigente_fuera_alcance"
        ]
        == "Cuentan con botiquín completo de primeros auxilios en todas las salas, en buena conservación y con insumos dentro de la fecha de vencimiento; fuera del alcance de los niños"
    )


def test_schema_cdi_aplica_matriz_de_textos():
    workday_choices = dict(CAMPOS_OPCIONES["tipo_jornada"])
    first_aid_choices = dict(CAMPOS_OPCIONES["estado_botiquin_primeros_auxilios"])
    water_access_choices = dict(CAMPOS_OPCIONES["acceso_agua"])
    internet_choices = dict(CAMPOS_OPCIONES["acceso_internet_personal"])
    month_choices = dict(FormularioCDIForm.base_fields["meses_funcionamiento"].choices)

    assert (
        workday_choices["simple_single_shift"]
        == "Jornada simple (un solo turno con un único grupo de niños)"
    )
    assert (
        first_aid_choices["completo_todas_salas_ok_vigente_fuera_alcance"]
        == "Cuentan con botiquín completo de primeros auxilios en todas las salas, en buena conservación y con insumos dentro de la fecha de vencimiento; fuera del alcance de los niños"
    )
    assert water_access_choices["caneria_dentro_cdi"] == "Por cañería dentro del CDI"
    assert (
        internet_choices["estable_sin_acceso_personal"]
        == "El CDI cuenta con un servicio de internet relativamente estable al que accede el personal"
    )
    assert month_choices["enero"] == "Enero"
    assert ETIQUETAS_CAMPOS["fecha_relevamiento"] == "Fecha de Relevamiento"
