from datetime import date

import pytest

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.forms import NominaCentroInfanciaDestinatariosForm
from core.models import Provincia


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


def _base_data(**extra):
    return {
        "estado": NominaCentroInfancia.ESTADO_ACTIVO,
        "apellido": "Torres",
        "nombre": "Luca",
        "fecha_nacimiento": "2021-07-01",
        "dni": "45123456",
        **extra,
    }


# ─────────────────────────────────────────────────────────
# Validación básica del formulario
# ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatariosFormValidation:

    def test_form_valido_con_datos_minimos(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(_base_data(), centro=centro)
        assert form.is_valid(), form.errors

    def test_form_invalido_sin_apellido(self, centro):
        data = _base_data()
        data.pop("apellido")
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert not form.is_valid()
        assert "apellido" in form.errors

    def test_form_invalido_sin_nombre(self, centro):
        data = _base_data()
        data.pop("nombre")
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert not form.is_valid()
        assert "nombre" in form.errors

    def test_form_invalido_fecha_nacimiento_incorrecta(self, centro):
        form = NominaCentroInfanciaDestinatariosForm(
            _base_data(fecha_nacimiento="2021-99-99"), centro=centro
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
        data = _base_data(
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
        data = _base_data(grupo_pertenencia=["africano", "indigena"])
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert set(nomina.grupo_pertenencia) == {"africano", "indigena"}

    def test_tipo_discapacidad_se_guarda_como_lista(self, centro, ciudadano):
        data = _base_data(tiene_discapacidad="si", tipo_discapacidad=["motora", "visual"])
        form = NominaCentroInfanciaDestinatariosForm(data, centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert "motora" in nomina.tipo_discapacidad

    def test_vacunacion_nomivac_se_guarda_como_dict(self, centro, ciudadano):
        data = _base_data(
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
        form = NominaCentroInfanciaDestinatariosForm(_base_data(), centro=centro)
        assert form.is_valid(), form.errors
        nomina = form.save(commit=False)
        nomina.centro = centro
        nomina.ciudadano = ciudadano
        nomina.save()
        nomina.refresh_from_db()
        assert isinstance(nomina.vacunacion_nomivac, dict)

    def test_vacunas_sin_dosis_no_se_incluyen_en_json(self, centro, ciudadano):
        data = _base_data(vacuna_bcg_dosis="1_dosis", vacuna_bcg_fecha="2022-01-10")
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
