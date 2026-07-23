from datetime import date

import pytest

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import (
    CentroDeInfancia,
    NominaCentroInfancia,
    NominaNacionalidad,
    NominaPais,
    Trabajador,
)
from centrodeinfancia.forms import NominaCentroInfanciaDestinatariosForm
from core.models import Localidad, Municipio, Provincia


@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Chubut")


@pytest.fixture
def centro(provincia):
    return CentroDeInfancia.objects.create(nombre="CDI Form Test", provincia=provincia)


@pytest.fixture
def ciudadano():
    return Ciudadano.objects.create(
        apellido="Torres",
        nombre="Luca",
        fecha_nacimiento=date(2021, 7, 1),
        documento=45123456,
    )


def _relacionados(centro):
    """Crea los objetos que el legajo necesita referenciar (catálogos y geografía).

    Los tests corren con TEST MIGRATE=False, así que las fixtures de países y
    nacionalidades no se cargan solas.
    """

    NominaPais.objects.get_or_create(nombre="Argentina")
    NominaNacionalidad.objects.get_or_create(nombre="Argentino")

    provincia, _ = Provincia.objects.get_or_create(nombre="Buenos Aires")
    municipio, _ = Municipio.objects.get_or_create(nombre="Moreno", provincia=provincia)
    localidad, _ = Localidad.objects.get_or_create(
        nombre="Paso del Rey", municipio=municipio
    )
    trabajador, _ = Trabajador.objects.get_or_create(
        centro=centro,
        nombre="Ana",
        apellido="Lopez",
    )
    return provincia, municipio, localidad, trabajador


def datos_validos(centro, **overrides):
    """Payload completo del legajo de destinatario: todos los campos obligatorios."""

    provincia, municipio, localidad, trabajador = _relacionados(centro)
    datos = {
        # Registro
        "estado": NominaCentroInfancia.ESTADO_ACTIVO,
        "tipo_registro": "alta",
        "fecha_registro": "2026-07-01",
        "trabajador_registra": str(trabajador.pk),
        # Datos del niño/a
        "apellido": "Torres",
        "nombre": "Luca",
        "fecha_nacimiento": "2021-07-01",
        "sexo": "Masculino",
        "tipo_documentacion": "dni_permanente",
        "dni": "45123456",
        "pais_nacimiento": "Argentina",
        "nacionalidad": "Argentino",
        "sala": "Sala Verde",
        # Responsable 1
        "responsable_legal_1_relacion": "madre",
        "responsable_legal_1_apellido": "Torres",
        "responsable_legal_1_nombre": "Laura",
        "responsable_legal_1_fecha_nacimiento": "1990-05-04",
        "responsable_legal_1_tipo_documentacion": "dni_permanente",
        "responsable_legal_1_dni": "30123456",
        "responsable_legal_1_pais_nacimiento": "Argentina",
        "responsable_legal_1_nacionalidad": "Argentino",
        "responsable_legal_1_sexo_registral": "mujer",
        "responsable_legal_1_nivel_educativo": "secundario_completo",
        "responsable_legal_1_consentimiento": "si",
        # Domicilio
        "calle_domicilio": "San Martín",
        "altura_domicilio": "1234",
        "tipo_barrio": "urbano",
        "provincia_domicilio": str(provincia.pk),
        "municipio_domicilio": str(municipio.pk),
        "localidad_domicilio": str(localidad.pk),
        # Cultura e identidad
        "grupo_pertenencia": ["ninguno"],
        "lenguajes": ["espanol_castellano"],
        "necesito_interprete": "no",
        # Discapacidad
        "tiene_discapacidad": "no",
        # Salud
        "cobertura_salud": "publica_exclusiva",
        "controles_sanitarios_ultimo_anio": "1",
        "calendario_vacunacion_al_dia": "true",
        # Nutrición
        "lactancia": "no_lactante",
        "alergias_alimentarias": ["leche_vaca"],
    }
    datos.update(overrides)
    return datos


# ─────────────────────────────────────────────────────────
# Validación básica del formulario
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatariosFormValidation:

    def test_form_valido_con_datos_minimos(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(
            datos_validos(centro), centro=centro
        )
        assert form.is_valid(), form.errors

    def test_form_invalido_sin_apellido(self, centro):
        data = datos_validos(centro)
        data.pop("apellido")
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert not form.is_valid()
        assert "apellido" in form.errors

    def test_form_invalido_sin_nombre(self, centro):
        data = datos_validos(centro)
        data.pop("nombre")
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert not form.is_valid()
        assert "nombre" in form.errors

    def test_form_invalido_fecha_nacimiento_incorrecta(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(
            datos_validos(centro, fecha_nacimiento="2021-99-99"), centro=centro
        )
        assert not form.is_valid()
        assert "fecha_nacimiento" in form.errors

    def test_tiene_28_campos_de_vacuna(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(centro=centro)
        vacuna_fields = [k for k in form.fields if k.startswith("vacuna_")]
        assert len(vacuna_fields) == 28

    def test_campos_dinamicos_vacuna_tienen_nombres_correctos(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(centro=centro)
        assert "vacuna_bcg_dosis" in form.fields
        assert "vacuna_bcg_fecha" in form.fields
        assert "vacuna_fiebre_amarilla_dosis" in form.fields
        assert "vacuna_fiebre_amarilla_fecha" in form.fields


# ─────────────────────────────────────────────────────────
# JSONField multiselects — guardado correcto
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatariosFormJsonFields:

    def test_alergias_alimentarias_se_guarda_como_lista(self, centro, ciudadano):
        data = datos_validos(
            centro,
            alergias_alimentarias=["leche_vaca", "tacc"],
        )
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert set(nomina.alergias_alimentarias) == {"leche_vaca", "tacc"}

    def test_grupo_pertenencia_se_guarda_como_lista(self, centro, ciudadano):
        data = datos_validos(centro, grupo_pertenencia=["africano", "asiatico"])
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert set(nomina.grupo_pertenencia) == {"africano", "asiatico"}

    def test_tipo_discapacidad_se_guarda_como_lista(self, centro, ciudadano):
        data = datos_validos(
            centro,
            tiene_discapacidad="si",
            tipo_discapacidad=["motora", "visual"],
            # Obligatorio cuando hay discapacidad (TC_102).
            recibe_apoyo_discapacidad="true",
        )
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert "motora" in nomina.tipo_discapacidad

    def test_vacunacion_nomivac_se_guarda_como_dict(self, centro, ciudadano):
        data = datos_validos(
            centro,
            vacuna_bcg_dosis="1_dosis",
            vacuna_bcg_fecha="2022-01-10",
            vacuna_triple_viral_dosis="2_dosis",
            vacuna_triple_viral_fecha="2023-06-15",
        )
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert isinstance(nomina.vacunacion_nomivac, dict)
        assert nomina.vacunacion_nomivac["bcg"]["dosis"] == "1_dosis"
        assert nomina.vacunacion_nomivac["bcg"]["fecha"] == "2022-01-10"
        assert nomina.vacunacion_nomivac["triple_viral"]["dosis"] == "2_dosis"

    def test_vacunacion_nomivac_vacio_guarda_dict_vacio(self, centro, ciudadano):
        form = NominaCentroInfanciaDestinatariosForm(
            datos_validos(centro), centro=centro
        )
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert isinstance(nomina.vacunacion_nomivac, dict)

    def test_vacunas_sin_dosis_no_se_incluyen_en_json(self, centro, ciudadano):
        data = datos_validos(
            centro, vacuna_bcg_dosis="1_dosis", vacuna_bcg_fecha="2022-01-10"
        )
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        # Solo bcg fue enviada, el resto no debe aparecer
        assert "bcg" in nomina.vacunacion_nomivac
        assert "triple_viral" not in nomina.vacunacion_nomivac


# ─────────────────────────────────────────────────────────
# Pre-población al editar
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatariosFormEdit:

    def test_jsonfields_se_precargan_al_editar(self, centro, ciudadano):
        nomina = NominaCentroInfancia.objects.create(
            centro=centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
            estado=NominaCentroInfancia.ESTADO_ACTIVO,
            alergias_alimentarias=["leche_vaca"],
            grupo_pertenencia=["migrante"],
            vacunacion_nomivac={"bcg": {"dosis": "1_dosis", "fecha": "2022-01-10"}},
        )
        form = NominaCentroInfanciaDestinatariosForm(instance=nomina, centro=centro)
        assert form.fields["alergias_alimentarias"].initial == ["leche_vaca"]
        assert form.fields["grupo_pertenencia"].initial == ["migrante"]
        # Campos dinámicos de vacuna deben precargarse
        assert form.fields["vacuna_bcg_dosis"].initial == "1_dosis"
        assert form.fields["vacuna_bcg_fecha"].initial == "2022-01-10"


# ─────────────────────────────────────────────────────────
# Validaciones reportadas por QA (tercera tanda)
# ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestValidacionesQA:
    """Casos de la planilla de QA del alta de niño/a en nómina."""

    def _form(self, centro, **overrides):
        return NominaCentroInfanciaDestinatariosForm(
            datos_validos(centro, **overrides), centro=centro
        )

    # TC_161: no se guarda un legajo incompleto
    @pytest.mark.parametrize(
        "campo",
        NominaCentroInfanciaDestinatariosForm.CAMPOS_OBLIGATORIOS,
    )
    def test_rechaza_campo_obligatorio_vacio(self, centro, campo):
        form = self._form(centro, **{campo: ""})
        assert not form.is_valid()
        assert campo in form.errors

    # TC_015/016/028/029: nombres y apellidos solo aceptan letras
    @pytest.mark.parametrize(
        "campo",
        NominaCentroInfanciaDestinatariosForm.CAMPOS_SOLO_LETRAS,
    )
    @pytest.mark.parametrize("valor", ["1234", "@@@"])
    def test_rechaza_numeros_y_simbolos_en_nombres(self, centro, campo, valor):
        form = self._form(centro, **{campo: valor})
        assert not form.is_valid()
        assert campo in form.errors

    def test_acepta_nombres_con_tildes_y_guiones(self, centro):
        form = self._form(centro, apellido="Sáenz-Peña", nombre="José María")
        assert form.is_valid(), form.errors

    # TC_021/032/046: DNI de 7 u 8 dígitos
    @pytest.mark.parametrize("valor", ["123", "123456789"])
    def test_rechaza_dni_fuera_de_rango(self, centro, valor):
        form = self._form(centro, dni=valor)
        assert not form.is_valid()
        assert "dni" in form.errors

    # TC_022/033/047: CUIT con dígito verificador
    @pytest.mark.parametrize("valor", ["12345", "123456789012", "00-00000000-0"])
    def test_rechaza_cuit_invalido(self, centro, valor):
        form = self._form(centro, cuit_nino=valor)
        assert not form.is_valid()
        assert "cuit_nino" in form.errors

    def test_acepta_cuit_valido(self, centro):
        form = self._form(centro, cuit_nino="20-44535030-4")
        assert form.is_valid(), form.errors

    # TC_017/026/030/044: fechas no futuras
    @pytest.mark.parametrize(
        "campo",
        ["fecha_nacimiento", "fecha_registro", "responsable_legal_1_fecha_nacimiento"],
    )
    def test_rechaza_fecha_futura(self, centro, campo):
        futuro = date(date.today().year + 5, 1, 1).isoformat()
        form = self._form(centro, **{campo: futuro})
        assert not form.is_valid()
        assert campo in form.errors

    # TC_017/030/044: fechas absurdamente antiguas (ej. 1800)
    def test_rechaza_fecha_nacimiento_de_1800(self, centro):
        form = self._form(centro, fecha_nacimiento="1800-01-01")
        assert not form.is_valid()
        assert "fecha_nacimiento" in form.errors

    # TC_134 y siguientes: la fecha de vacunación tampoco puede ser futura
    def test_rechaza_fecha_de_vacuna_futura(self, centro):
        futuro = date(date.today().year + 5, 1, 1).isoformat()
        form = self._form(centro, vacuna_bcg_dosis="1_dosis", vacuna_bcg_fecha=futuro)
        assert not form.is_valid()
        assert "vacuna_bcg_fecha" in form.errors

    # TC_057: piso solo admite números
    def test_rechaza_piso_no_numerico(self, centro):
        form = self._form(centro, piso_domicilio="ABC")
        assert not form.is_valid()
        assert "piso_domicilio" in form.errors

    # TC_056: altura de hasta 5 dígitos
    def test_rechaza_altura_demasiado_larga(self, centro):
        form = self._form(centro, altura_domicilio="123456")
        assert not form.is_valid()
        assert "altura_domicilio" in form.errors

    # TC_104: número de CUD solo numérico
    def test_rechaza_numero_cud_no_numerico(self, centro):
        form = self._form(
            centro,
            tiene_discapacidad="si",
            recibe_apoyo_discapacidad="true",
            posee_cud="true",
            numero_cud="ABC123",
        )
        assert not form.is_valid()
        assert "numero_cud" in form.errors

    # TC_104: si tiene CUD, el número es obligatorio
    def test_numero_cud_obligatorio_si_posee_cud(self, centro):
        form = self._form(
            centro,
            tiene_discapacidad="si",
            recibe_apoyo_discapacidad="true",
            posee_cud="true",
            numero_cud="",
        )
        assert not form.is_valid()
        assert "numero_cud" in form.errors

    # TC_102: si hay discapacidad, los apoyos son obligatorios
    def test_apoyos_obligatorios_si_tiene_discapacidad(self, centro):
        form = self._form(centro, tiene_discapacidad="si", recibe_apoyo_discapacidad="")
        assert not form.is_valid()
        assert "recibe_apoyo_discapacidad" in form.errors

    # TC_101/TS003: "No sabe" no se combina con otros tipos de discapacidad
    def test_tipo_discapacidad_no_sabe_es_excluyente(self, centro):
        form = self._form(
            centro,
            tiene_discapacidad="si",
            recibe_apoyo_discapacidad="true",
            tipo_discapacidad=["no_sabe", "motora"],
        )
        assert not form.is_valid()
        assert "tipo_discapacidad" in form.errors

    # TC_068: "Ninguno" no se combina con otros grupos de pertenencia
    def test_grupo_pertenencia_ninguno_es_excluyente(self, centro):
        form = self._form(centro, grupo_pertenencia=["ninguno", "africano"])
        assert not form.is_valid()
        assert "grupo_pertenencia" in form.errors

    # TC_034/048: teléfono de 6 a 15 dígitos (criterio único del sistema)
    @pytest.mark.parametrize("valor", ["12345", "1234567890123456"])
    def test_rechaza_telefono_invalido(self, centro, valor):
        form = self._form(centro, responsable_legal_1_telefono=valor)
        assert not form.is_valid()
        assert "responsable_legal_1_telefono" in form.errors

    @pytest.mark.parametrize("valor", ["1122334455", "47742015"])
    def test_acepta_telefono_valido(self, centro, valor):
        # El teléfono del responsable es entero en el modelo: no admite guiones.
        form = self._form(centro, responsable_legal_1_telefono=valor)
        assert form.is_valid(), form.errors

    @pytest.mark.parametrize("valor", ["4774-2015", "011-4774-2015"])
    def test_acepta_telefono_con_guiones_en_campo_de_texto(self, centro, valor):
        form = self._form(centro, adulto_responsable_telefono=valor)
        assert form.is_valid(), form.errors

    @pytest.mark.parametrize("valor", ["12345", "1234567890123456"])
    def test_rechaza_telefono_de_texto_fuera_de_rango(self, centro, valor):
        form = self._form(centro, adulto_responsable_telefono=valor)
        assert not form.is_valid()
        assert "adulto_responsable_telefono" in form.errors

    # Campos ocultos por pedido de producto: no se exponen en el formulario
    @pytest.mark.parametrize(
        "campo", NominaCentroInfanciaDestinatariosForm.CAMPOS_OCULTOS
    )
    def test_campos_ocultos_no_estan_en_el_formulario(self, centro, campo):
        form = NominaCentroInfanciaDestinatariosForm(centro=centro)
        assert campo not in form.fields

    def test_campos_ocultos_siguen_en_el_modelo(self):
        # Se ocultan del form pero no se borran: los datos ya cargados se conservan.
        nombres = {f.name for f in NominaCentroInfancia._meta.get_fields()}
        for campo in NominaCentroInfanciaDestinatariosForm.CAMPOS_OCULTOS:
            assert campo in nombres
