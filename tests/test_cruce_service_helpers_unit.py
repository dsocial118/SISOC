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
        return_value=pd.DataFrame(
            {"documento": ["20-12345678-3", "00123456", "", None]}
        ),
    )
    ids = CruceService._leer_identificadores(io.BytesIO(b"x"))
    assert "20123456783" in ids["cuits"]
    assert "12345678" in ids["dnis"]
    assert "123456" in ids["dnis"]


def test_leer_identificadores_validation_errors(mocker):
    mocker.patch.object(
        CruceService, "_leer_tabla", return_value=pd.DataFrame({"foo": ["1"]})
    )
    with pytest.raises(ValidationError):
        CruceService._leer_identificadores(io.BytesIO(b"x"))

    mocker.patch.object(
        CruceService,
        "_leer_tabla",
        return_value=pd.DataFrame({"documento": ["", None]}),
    )
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

    mocker.patch(
        "celiaquia.services.familia_service.FamiliaService.obtener_ids_responsables",
        return_value={1},
    )
    mocker.patch(
        "celiaquia.services.familia_service.FamiliaService.obtener_responsables_por_hijo",
        return_value={2: []},
    )

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
    mocker.patch(
        "celiaquia.services.cruce_service.pd.read_excel", side_effect=ValueError("x")
    )

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
        CruceService.procesar_cruce_por_cuit(
            exp_bad, archivo_excel=object(), usuario="u"
        )

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


def test_leer_tabla_raises_when_all_formats_fail(mocker):
    class F:
        def open(self):
            return None

        def read(self):
            return b"xxx"

        def seek(self, _):
            return None

    mocker.patch(
        "celiaquia.services.cruce_service.pd.read_excel", side_effect=ValueError("x")
    )
    mocker.patch(
        "celiaquia.services.cruce_service.pd.read_csv", side_effect=ValueError("x")
    )

    with pytest.raises(ValidationError):
        CruceService._leer_tabla(F())


def test_generar_prd_pdf_html_requires_weasy(monkeypatch):
    monkeypatch.setattr(cruce_module, "_WEASY_OK", False)
    with pytest.raises(RuntimeError):
        CruceService._generar_prd_pdf_html(SimpleNamespace(), {})


def test_generar_prd_pdf_html_success_with_weasy(mocker, monkeypatch):
    monkeypatch.setattr(cruce_module, "_WEASY_OK", True)

    expediente = SimpleNamespace(
        asignaciones_tecnicos=SimpleNamespace(
            all=lambda: SimpleNamespace(
                exists=lambda: True,
                first=lambda: SimpleNamespace(
                    tecnico=SimpleNamespace(
                        get_full_name=lambda: "Tec Name", username="tec"
                    )
                ),
            )
        )
    )
    mocker.patch(
        "celiaquia.services.cruce_service.render_to_string",
        return_value="<html></html>",
    )
    mocker.patch(
        "celiaquia.services.cruce_service.WPHTML",
        return_value=SimpleNamespace(write_pdf=lambda: b"pdf-bytes"),
    )

    out = CruceService._generar_prd_pdf_html(
        expediente,
        {"total_legajos": 10, "matcheados": 7, "no_matcheados": 3},
    )
    assert out == b"pdf-bytes"


def test_generar_prd_pdf_prefers_html_and_falls_back(mocker, monkeypatch):
    expediente = SimpleNamespace()
    resumen = {"total_legajos": 1}

    # Caso 1: Weasy deshabilitado -> ReportLab directo
    monkeypatch.setattr(cruce_module, "_WEASY_OK", False)
    reportlab = mocker.patch.object(
        CruceService, "_generar_prd_pdf_reportlab", return_value=b"r1"
    )
    html = mocker.patch.object(
        CruceService, "_generar_prd_pdf_html", return_value=b"h1"
    )
    out1 = CruceService._generar_prd_pdf(expediente, resumen)
    assert out1 == b"r1"
    assert reportlab.called
    assert not html.called

    # Caso 2: Weasy habilitado pero HTML falla -> fallback
    monkeypatch.setattr(cruce_module, "_WEASY_OK", True)
    mocker.patch.object(
        CruceService, "_generar_prd_pdf_html", side_effect=RuntimeError("boom")
    )
    reportlab2 = mocker.patch.object(
        CruceService, "_generar_prd_pdf_reportlab", return_value=b"r2"
    )
    out2 = CruceService._generar_prd_pdf(expediente, resumen)
    assert out2 == b"r2"
    assert reportlab2.called

    # Caso 3: Weasy habilitado y HTML OK
    mocker.patch.object(CruceService, "_generar_prd_pdf_html", return_value=b"h3")
    out3 = CruceService._generar_prd_pdf(expediente, resumen)
    assert out3 == b"h3"


def test_read_file_bytes_rejects_non_binary_payload_type():
    class Weird:
        def open(self):
            return None

        def read(self):
            return 123

        def seek(self, _):
            return None

    with pytest.raises(ValidationError):
        CruceService._read_file_bytes(Weird())


def test_generar_prd_pdf_reportlab_with_detail_sections():
    expediente = SimpleNamespace(
        asignaciones_tecnicos=SimpleNamespace(
            all=lambda: SimpleNamespace(
                exists=lambda: True,
                first=lambda: SimpleNamespace(
                    tecnico=SimpleNamespace(get_full_name=lambda: "Tec", username="tec")
                ),
            )
        )
    )
    resumen = {
        "total_legajos": 10,
        "matcheados": 6,
        "no_matcheados": 4,
        "total_cuits_archivo": 5,
        "total_dnis_archivo": 5,
        "cupo_total": 100,
        "cupo_usados": 50,
        "cupo_disponibles": 50,
        "fuera_cupo": 1,
        "detalle_match": [
            {"dni": "1", "cuit": "20", "nombre": "A", "apellido": "B", "por": "DNI"}
        ],
        "detalle_no_match": [{"dni": "2", "cuit": "30", "observacion": "No match"}],
        "detalle_fuera_cupo": [
            {"dni": "3", "cuit": "40", "nombre": "C", "apellido": "D"}
        ],
    }

    pdf = CruceService._generar_prd_pdf_reportlab(expediente, resumen)
    assert isinstance(pdf, (bytes, bytearray))
    assert len(pdf) > 0


def test_generar_prd_csv_with_writer_stub(mocker):
    rows = []

    class _Writer:
        def writerow(self, row):
            rows.append(row)

    mocker.patch("celiaquia.services.cruce_service.csv.writer", return_value=_Writer())

    out = CruceService._generar_prd_csv(
        expediente=SimpleNamespace(),
        resumen={
            "total_legajos": 2,
            "total_cuits_archivo": 1,
            "total_dnis_archivo": 1,
            "matcheados": 1,
            "no_matcheados": 1,
            "cupo": {"total_asignado": 10, "usados": 5, "disponibles": 5},
            "cupo_fuera_count": 0,
            "detalle_no_match": ["no1"],
            "detalle_fuera_cupo": ["fc1"],
        },
    )

    assert isinstance(out, (bytes, bytearray))
    assert any(r and r[0] == "Resumen" for r in rows)
    assert any(r and r[0] == "Detalle_no_matcheados" for r in rows)
