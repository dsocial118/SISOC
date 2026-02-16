"""Tests for test importacion service helpers unit."""

from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import importacion_service as module

pytestmark = pytest.mark.django_db


class _DummyFile:
    def __init__(self, raw: bytes, name="data.csv"):
        self._raw = raw
        self.name = name
        self._bio = BytesIO(raw)

    def open(self):
        return None

    def seek(self, pos):
        self._bio.seek(pos)

    def read(self):
        return self._bio.read()


def test_norm_col_estado_tipo_doc_and_edad(mocker):
    assert module._norm_col("  NOMBRE COMPLETO ") == "nombre_completo"
    assert module._norm_col("***") == "columna"
    assert module._get_tipo_documento("20123456783") == module.Ciudadano.DOCUMENTO_CUIT
    assert module._get_tipo_documento("12345678") == module.Ciudadano.DOCUMENTO_DNI

    module._estado_doc_pendiente_id.cache_clear()
    mocker.patch(
        "celiaquia.services.importacion_service.EstadoLegajo.objects.only",
        return_value=SimpleNamespace(get=lambda **k: SimpleNamespace(id=7)),
    )
    assert module._estado_doc_pendiente_id() == 7

    class Missing(Exception):
        pass

    module._estado_doc_pendiente_id.cache_clear()
    mocker.patch("celiaquia.services.importacion_service.EstadoLegajo.DoesNotExist", Missing)
    mocker.patch(
        "celiaquia.services.importacion_service.EstadoLegajo.objects.only",
        return_value=SimpleNamespace(get=lambda **k: (_ for _ in ()).throw(Missing())),
    )
    with pytest.raises(ValidationError):
        module._estado_doc_pendiente_id()

    adulto = date.today() - timedelta(days=40 * 365)
    menor = date.today() - timedelta(days=10 * 365)
    ok, _w, err = module.validar_edad_responsable(adulto, menor)
    assert ok is True and err is None

    ok2, _w2, err2 = module.validar_edad_responsable(menor, adulto)
    assert ok2 is False and "18" in err2


def test_generar_plantilla_and_preview_csv(mocker):
    blob = module.ImportacionService.generar_plantilla_excel()
    assert isinstance(blob, bytes)
    df = pd.read_excel(BytesIO(blob), engine="openpyxl")
    assert "apellido" in df.columns

    raw_csv = (
        "municipio,localidad,nombre,nombre\n"
        "1,2,Juan,Perez\n"
        "3,4,Ana,Lopez\n"
    ).encode("utf-8")
    f = _DummyFile(raw_csv, name="datos.csv")

    mocker.patch(
        "celiaquia.services.importacion_service.Municipio.objects.get",
        side_effect=lambda pk: SimpleNamespace(nombre=f"M{pk}"),
    )
    mocker.patch(
        "celiaquia.services.importacion_service.Localidad.objects.get",
        side_effect=lambda pk: SimpleNamespace(nombre=f"L{pk}"),
    )

    preview = module.ImportacionService.preview_excel(f, max_rows="1")
    assert preview["headers"][0] == "ID"
    assert preview["shown_rows"] == 1
    assert preview["rows"][0]["ID"] == 1
    assert preview["rows"][0]["municipio"] == "M1"
    assert preview["rows"][0]["localidad"] == "L2"


def test_preview_excel_parses_all_and_semicolon_fallback(mocker):
    data_semicolon = "nombre;municipio\nJuan;1\n".encode("utf-8")
    f = _DummyFile(data_semicolon, name="otro.txt")

    # force utf-8 comma read failure so it uses sep=';'
    def _read_csv(*_a, **kwargs):
        if kwargs.get("sep") == ";":
            return pd.DataFrame({"nombre": ["Juan"], "municipio": ["1"]})
        raise ValueError("bad csv")

    mocker.patch("celiaquia.services.importacion_service.pd.read_csv", side_effect=_read_csv)
    mocker.patch(
        "celiaquia.services.importacion_service.Municipio.objects.get",
        return_value=SimpleNamespace(nombre="M1"),
    )

    out = module.ImportacionService.preview_excel(f, max_rows="all")
    assert out["shown_rows"] == 1
    assert out["total_rows"] == 1


def test_validar_edad_exception_and_preview_limit_variants(mocker):
    ok, warnings, err = module.validar_edad_responsable("x", date.today())
    assert ok is True
    assert warnings == []
    assert err is None

    raw_csv = "nombre,municipio\nJuan,1\n".encode("utf-8")
    f = _DummyFile(raw_csv, name="limites.csv")
    mocker.patch(
        "celiaquia.services.importacion_service.Municipio.objects.get",
        return_value=SimpleNamespace(nombre="M1"),
    )

    out_zero = module.ImportacionService.preview_excel(f, max_rows="0")
    assert out_zero["shown_rows"] == 1

    f2 = _DummyFile(raw_csv, name="limites2.csv")
    out_todos = module.ImportacionService.preview_excel(f2, max_rows="todos")
    assert out_todos["shown_rows"] == 1


def test_importar_legajos_raises_validation_on_invalid_excel(mocker):
    class _F:
        def open(self):
            return None

        def seek(self, _pos):
            return None

        def read(self):
            return b"not-an-excel"

    expediente = SimpleNamespace()
    usuario = SimpleNamespace()

    mocker.patch(
        "celiaquia.services.importacion_service.pd.read_excel",
        side_effect=ValueError("broken file"),
    )

    with pytest.raises(ValidationError):
        module.ImportacionService.importar_legajos_desde_excel(
            expediente,
            _F(),
            usuario,
        )
