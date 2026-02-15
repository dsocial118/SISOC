"""Tests for test cruce service helpers unit."""

import io
from types import SimpleNamespace

import pandas as pd
import pytest
from django.core.exceptions import ValidationError

from celiaquia.services.cruce_service import CruceService
from celiaquia.services import cruce_service as cruce_module

pytestmark = pytest.mark.django_db


def test_normalization_and_cuit_resolution():
    assert CruceService.normalize_cuit_str("20-12345678-3") == "20123456783"
    assert CruceService.normalize_dni_str("0012.345.678") == "12345678"
    assert CruceService.extraer_dni_de_cuit("20123456783") == "12345678"
    assert CruceService.extraer_dni_de_cuit("123") == ""

    ciudadano = SimpleNamespace(cuit="20-12345678-3", documento="999")
    assert CruceService.resolver_cuit_ciudadano(ciudadano) == "20123456783"

    ciudadano2 = SimpleNamespace(documento="20-12345678-3")
    assert CruceService.resolver_cuit_ciudadano(ciudadano2) == "20123456783"

    ciudadano3 = SimpleNamespace(documento="12345678")
    assert CruceService.resolver_cuit_ciudadano(ciudadano3) == ""


def test_read_file_bytes_variants_and_errors():
    assert CruceService._read_file_bytes(b"abc") == b"abc"
    assert CruceService._read_file_bytes(bytearray(b"abc")) == b"abc"

    with pytest.raises(ValidationError):
        CruceService._read_file_bytes("/tmp/x.csv")

    class F:
        def open(self):
            return None

        def read(self):
            return "hola"

        def seek(self, _):
            return None

    assert CruceService._read_file_bytes(F()) == b"hola"

    class Bad:
        def open(self):
            return None

        def read(self):
            raise RuntimeError("boom")

        def seek(self, _):
            return None

    with pytest.raises(ValidationError):
        CruceService._read_file_bytes(Bad())


def test_col_preferencias_and_identificadores(mocker):
    df = pd.DataFrame(columns=["documento", "otro"])
    col = CruceService._col_por_preferencias(df, {"documento", "dni"}, "doc")
    assert col == "documento"

    df2 = pd.DataFrame(columns=["id_documento"])
    col2 = CruceService._col_por_preferencias(df2, {"x"}, "documento")
    assert col2 == "id_documento"

    mocker.patch.object(
        CruceService,
        "_leer_tabla",
        return_value=pd.DataFrame({"documento": ["20-12345678-3", "00123456", "", None]}),
    )
    ids = CruceService._leer_identificadores(io.BytesIO(b"x"))
    assert "20123456783" in ids["cuits"]
    assert "12345678" in ids["dnis"]
    assert "123456" in ids["dnis"]


def test_leer_identificadores_validation_errors(mocker):
    mocker.patch.object(CruceService, "_leer_tabla", return_value=pd.DataFrame({"foo": ["1"]}))
    with pytest.raises(ValidationError):
        CruceService._leer_identificadores(io.BytesIO(b"x"))

    mocker.patch.object(CruceService, "_leer_tabla", return_value=pd.DataFrame({"documento": ["", None]}))
    with pytest.raises(ValidationError):
        CruceService._leer_identificadores(io.BytesIO(b"x"))


def test_generar_nomina_sintys_excel_without_db(mocker):
    class Legajo:
        def __init__(self, cid, documento, nombre, apellido):
            self.ciudadano = SimpleNamespace(
                id=cid,
                documento=documento,
                nombre=nombre,
                apellido=apellido,
                get_tipo_documento_display=lambda: "DNI",
            )
            self.ciudadano_id = cid

    class Qs(list):
        def select_related(self, *_args, **_kwargs):
            return self

        def values_list(self, *_args, **_kwargs):
            return [x.ciudadano_id for x in self]

    qs = Qs([Legajo(1, "20123456783", "A", "B"), Legajo(2, "12345678", "C", "D")])
    expediente = SimpleNamespace(expediente_ciudadanos=qs)

    mocker.patch("celiaquia.services.familia_service.FamiliaService.obtener_ids_responsables", return_value={1})
    mocker.patch("celiaquia.services.familia_service.FamiliaService.obtener_responsables_por_hijo", return_value={2: []})

    data = CruceService.generar_nomina_sintys_excel(expediente)
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 0


def test_leer_tabla_csv_fallback_and_prd_csv_generation(mocker):
    """Table reader should fallback to CSV and PRD CSV should include summary sections."""

    class F:
        def __init__(self):
            self._b = io.BytesIO(b"documento;nombre\n20123456783;A\n")

        def open(self):
            return None

        def read(self):
            return self._b.read()

        def seek(self, x):
            return self._b.seek(x)

    # force excel/csv comma fail, then csv semicolon success
    mocker.patch("celiaquia.services.cruce_service.pd.read_excel", side_effect=ValueError("x"))

    def _read_csv(_bio, dtype=str, sep=","):
        if sep == ";":
            return pd.DataFrame({"documento": ["20123456783"], "nombre": ["A"]})
        raise ValueError("bad")

    mocker.patch("celiaquia.services.cruce_service.pd.read_csv", side_effect=_read_csv)
    df = CruceService._leer_tabla(F())
    assert "documento" in df.columns

    with pytest.raises(TypeError):
        CruceService._generar_prd_csv(
            expediente=SimpleNamespace(),
            resumen={
                "total_legajos": 2,
                "total_cuits_archivo": 1,
                "total_dnis_archivo": 1,
                "matcheados": 1,
                "no_matcheados": 1,
                "cupo": {"total_asignado": 10, "usados": 5, "disponibles": 5},
                "cupo_fuera_count": 0,
                "detalle_no_match": ["x"],
                "detalle_fuera_cupo": ["y"],
            },
        )


def test_procesar_cruce_validations(mocker):
    """Cruce should reject invalid expediente state and missing provincial cupo config."""
    exp_bad = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    with pytest.raises(ValidationError):
        CruceService.procesar_cruce_por_cuit(exp_bad, archivo_excel=object(), usuario="u")

    exp = SimpleNamespace(
        id=1,
        estado=SimpleNamespace(nombre="ASIGNADO"),
        provincia="P",
        save=mocker.Mock(),
    )
    mocker.patch(
        "celiaquia.services.cruce_service.CupoService.metrics_por_provincia",
        side_effect=cruce_module.CupoNoConfigurado("sin cupo"),
    )
    with pytest.raises(ValidationError):
        CruceService.procesar_cruce_por_cuit(exp, archivo_excel=object(), usuario="u")
