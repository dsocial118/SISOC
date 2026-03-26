"""Tests for test importacion service helpers unit."""

from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from celiaquia.services import importacion_service as module
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RegistroErroneo,
)
from ciudadanos.models import Ciudadano, GrupoFamiliar

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


def _crear_expediente_test():
    idx = get_user_model().objects.count() + 1
    user = get_user_model().objects.create_user(
        username=f"import_exp_user_{idx}",
        email=f"import_exp_user_{idx}@example.com",
        password="testpass123",
    )
    estado = EstadoExpediente.objects.create(
        nombre=f"estado_{EstadoExpediente.objects.count() + 1}"
    )
    return Expediente.objects.create(usuario_provincia=user, estado=estado)


def _crear_estado_legajo_test():
    return EstadoLegajo.objects.create(
        nombre=f"legajo_{EstadoLegajo.objects.count()+1}"
    )


def _crear_ciudadano_test(documento):
    return Ciudadano.objects.create(
        apellido=f"Apellido{documento}",
        nombre=f"Nombre{documento}",
        fecha_nacimiento=date(2000, 1, 1),
        documento=documento,
    )


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
    mocker.patch(
        "celiaquia.services.importacion_service.EstadoLegajo.DoesNotExist", Missing
    )
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
        "municipio,localidad,nombre,nombre\n" "1,2,Juan,Perez\n" "3,4,Ana,Lopez\n"
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

    mocker.patch(
        "celiaquia.services.importacion_service.pd.read_csv", side_effect=_read_csv
    )
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


def test_importacion_helpers_normalizan_dataframe_y_precargas(mocker):
    df = pd.DataFrame(
        [
            {
                " Nombre ": " Ana ",
                "Fecha de Nacimiento": pd.Timestamp("2020-01-02"),
                "Municipio": "1.0",
                "Localidad": "2",
                "Sexo": "Masculino",
                "Nacionalidad": "Argentina",
                "NOMBRE_RESPONSABLE": " Bea ",
                "NOMBRE_REPSONSABLE": " Se pisa ",
            }
        ]
    )
    out = module._normalizar_dataframe_importacion(df)

    assert out.iloc[0]["nombre"] == "Ana"
    assert out.iloc[0]["fecha_nacimiento"] == date(2020, 1, 2)
    assert out.iloc[0]["nombre_responsable"] == "Bea"
    assert list(out.columns).count("nombre_responsable") == 1

    ids = module._colectar_ids_y_nombres_importacion(out)
    assert ids["municipio_ids"] == {1}
    assert ids["localidad_ids"] == {2}
    assert ids["sexos_nombres"] == {"masculino"}
    assert ids["nacionalidades_nombres"] == {"argentina"}

    class _FakeMunicipiosQS(list):
        def filter(self, provincia_id=None, **_kwargs):
            if provincia_id is None:
                return self
            return [x for x in self if x.provincia_id == provincia_id]

    mocker.patch(
        "celiaquia.services.importacion_service.Municipio.objects.filter",
        return_value=_FakeMunicipiosQS(
            [
                SimpleNamespace(pk=1, provincia_id=7),
                SimpleNamespace(pk=3, provincia_id=8),
            ]
        ),
    )
    mocker.patch(
        "celiaquia.services.importacion_service.Localidad.objects.filter",
        return_value=[SimpleNamespace(pk=2)],
    )
    mocker.patch(
        "celiaquia.services.importacion_service.Sexo.objects.all",
        return_value=[
            SimpleNamespace(id=1, sexo="Masculino"),
            SimpleNamespace(id=2, sexo="Femenino"),
        ],
    )

    precargas = module._precargar_datos_importacion(out, provincia_usuario_id=7)
    assert precargas["municipios_cache"] == {1: 1}
    assert precargas["localidades_cache"] == {2: 2}
    assert precargas["sexos_cache"]["masculino"] == 1
    assert precargas["sexos_cache"]["f"] == 2


def test_consolida_beneficiario_que_tambien_es_responsable():
    expediente = _crear_expediente_test()
    estado_legajo = _crear_estado_legajo_test()
    ciudadano_responsable = _crear_ciudadano_test(33000001)
    ciudadano_hijo = _crear_ciudadano_test(33000002)

    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano_responsable,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )

    GrupoFamiliar.objects.create(
        ciudadano_1=ciudadano_responsable,
        ciudadano_2=ciudadano_hijo,
        vinculo=GrupoFamiliar.RELACION_PADRE,
    )

    warnings = []
    module._consolidar_beneficiarios_que_son_responsables(expediente, warnings)
    legajo.refresh_from_db()

    assert legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
    assert warnings == [
        {
            "fila": "general",
            "campo": "consolidacion_roles",
            "detalle": "Se actualizaron 1 beneficiarios a doble rol",
        }
    ]


def test_importacion_helpers_payload_row_and_defaults_validation():
    warnings = []

    def _add_warning(fila, campo, detalle):
        warnings.append((fila, campo, detalle))

    def _validar_documento(valor, _campo, _fila):
        if not valor.isdigit():
            raise ValidationError("solo digitos")

    row = {
        "nombre": " Ana ",
        "apellido": " Perez ",
        "documento": "20-12345678-3",
        "telefono": "341-555-0000",
        "fecha_nacimiento": "2000-01-01",
        "otro": "nan",
    }
    payload = module._build_payload_importacion_from_row(
        row=row,
        numeric_fields={"documento", "telefono"},
        offset=2,
        validar_documento=_validar_documento,
        add_warning=_add_warning,
    )

    assert payload["nombre"] == "Ana"
    assert payload["apellido"] == "Perez"
    assert payload["documento"] == "20123456783"
    assert payload["telefono"] == "3415550000"
    assert payload["otro"] is None
    assert warnings == []

    with pytest.raises(ValidationError):
        module._build_payload_importacion_from_row(
            row={"telefono": "abc"},
            numeric_fields={"telefono"},
            offset=2,
            validar_documento=_validar_documento,
            add_warning=_add_warning,
        )
    payload.update(
        {
            "sexo": "M",
            "nacionalidad": "Argentina",
            "municipio": "1",
            "localidad": "2",
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "1980-01-01",
            "sexo_responsable": "F",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": "Centro",
        }
    )

    module._aplicar_defaults_y_validar_payload_importacion(
        payload, provincia_usuario_id=7
    )
    assert payload["provincia"] == 7
    assert payload["tipo_documento"] == module.Ciudadano.DOCUMENTO_CUIT

    with pytest.raises(ValidationError):
        module._aplicar_defaults_y_validar_payload_importacion(
            {"nombre": "Ana", "documento": "123"}, provincia_usuario_id=None
        )


def test_importacion_helpers_normalizar_enriquecer_payload(mocker):
    warnings = []

    def _add_warning(fila, campo, detalle):
        warnings.append((fila, campo, detalle))

    def _to_date(value):
        assert value == "2000-01-01"
        return date(2000, 1, 1)

    def _normalizar_sexo(value):
        return {"M": 1, "m": 1}.get(value)

    def _nacionalidad_filter(**kwargs):
        pk = kwargs.get("pk")
        value = kwargs.get("nacionalidad__iexact")
        if pk == 9:
            return SimpleNamespace(first=lambda: SimpleNamespace(pk=9))
        if value == "Argentina":
            return SimpleNamespace(first=lambda: SimpleNamespace(pk=1))
        return SimpleNamespace(first=lambda: None)

    mocker.patch(
        "core.models.Nacionalidad.objects.filter",
        side_effect=_nacionalidad_filter,
    )

    payload = {
        "fecha_nacimiento": "2000-01-01",
        "municipio": "1.0",
        "localidad": "2",
        "sexo": "M",
        "nacionalidad": "Argentina",
        "email": "ana@example.com",
        "telefono": "12345678",
    }
    module._normalizar_enriquecer_payload_importacion(
        payload=payload,
        offset=3,
        add_warning=_add_warning,
        to_date=_to_date,
        municipios_cache={1: 101},
        localidades_cache={2: 202},
        normalizar_sexo=_normalizar_sexo,
    )

    assert payload["fecha_nacimiento"] == date(2000, 1, 1)
    assert payload["municipio"] == 101
    assert payload["localidad"] == 202
    assert payload["sexo"] == 1
    assert payload["nacionalidad"] == 1
    assert payload["email"] == "ana@example.com"
    assert warnings == []

    with pytest.raises(ValidationError):
        module._normalizar_enriquecer_payload_importacion(
            payload={
                "fecha_nacimiento": "2000-01-01",
                "municipio": "1.0",
                "localidad": "2",
                "sexo": "M",
                "nacionalidad": "Arg",
                "email": "ana@example.com",
                "telefono": "12345678",
            },
            offset=3,
            add_warning=_add_warning,
            to_date=_to_date,
            municipios_cache={1: 101},
            localidades_cache={2: 202},
            normalizar_sexo=_normalizar_sexo,
        )

    with pytest.raises(ValidationError):
        module._normalizar_enriquecer_payload_importacion(
            payload={
                "fecha_nacimiento": "2000-01-01",
                "municipio": "1.0",
                "localidad": "2",
                "sexo": "M",
                "nacionalidad": "Argentina",
                "email": "correo-invalido",
                "telefono": "12345678",
            },
            offset=3,
            add_warning=_add_warning,
            to_date=_to_date,
            municipios_cache={1: 101},
            localidades_cache={2: 202},
            normalizar_sexo=_normalizar_sexo,
        )

    bad_phone_payload = {
        "fecha_nacimiento": "2000-01-01",
        "sexo": "M",
        "telefono": "1234",
    }
    with pytest.raises(ValidationError):
        module._normalizar_enriquecer_payload_importacion(
            payload=bad_phone_payload,
            offset=4,
            add_warning=_add_warning,
            to_date=_to_date,
            municipios_cache={},
            localidades_cache={},
            normalizar_sexo=_normalizar_sexo,
        )


def test_importacion_helpers_responsable_payload_and_same_document():
    def _add_error(_fila, _campo, detalle):
        raise ValidationError(detalle)

    payload = {
        "apellido_responsable": "Perez",
        "nombre_responsable": "Ana",
        "fecha_nacimiento_responsable": "2001-01-01",
        "telefono_responsable": "3415550000",
        "email_responsable": "ana@example.com",
        "documento_responsable": "20123456783",
        "sexo_responsable": "F",
        "domicilio_responsable": "Calle Resp 123",
        "localidad_responsable": "Rosario",
        "documento": "20123456783",
    }

    responsable_payload = module._build_responsable_payload_importacion(
        payload=payload,
        provincia_usuario_id=7,
        offset=2,
        add_error=_add_error,
    )
    module._agregar_sexo_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        normalizar_sexo=lambda v: 2 if v == "F" else None,
    )

    assert responsable_payload["tipo_documento"] == module.Ciudadano.DOCUMENTO_CUIT
    assert responsable_payload["provincia"] == 7
    assert responsable_payload["sexo"] == 2
    assert module._es_mismo_documento_responsable_importacion(payload) is True

    with pytest.raises(ValidationError):
        module._build_responsable_payload_importacion(
            payload={"nombre_responsable": "Ana"},
            provincia_usuario_id=7,
            offset=2,
            add_error=_add_error,
        )


def test_importacion_helpers_responsable_enriquecimiento_y_relacion(mocker):
    warnings = []

    def _add_warning(fila, campo, detalle):
        warnings.append((fila, campo, detalle))

    class _LocalidadesQS:
        def filter(self, **kwargs):
            if "municipio__provincia_id" in kwargs:
                return self
            if kwargs == {"nombre__iexact": "Rosario"}:
                return [SimpleNamespace(pk=11, municipio=SimpleNamespace(pk=22))]
            if kwargs == {"nombre__icontains": "Rosario"}:
                return [SimpleNamespace(pk=11, municipio=SimpleNamespace(pk=22))]
            return []

    mocker.patch(
        "celiaquia.services.importacion_service.Localidad.objects.select_related",
        return_value=_LocalidadesQS(),
    )

    responsable_payload = {"fecha_nacimiento": "2001-02-03"}
    payload = {
        "domicilio_responsable": "San Martin 1234",
        "localidad_responsable": "Rosario",
    }

    module._enriquecer_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        provincia_usuario_id=7,
        offset=3,
        add_warning=_add_warning,
        to_date=lambda value: date.fromisoformat(value),
    )

    assert responsable_payload["calle"] == "San Martin"
    assert responsable_payload["altura"] == "1234"
    assert responsable_payload["localidad"] == 11
    assert responsable_payload["municipio"] == 22
    assert responsable_payload["fecha_nacimiento"] == date(2001, 2, 3)
    assert warnings == []

    relaciones = []
    pares = set()
    assert (
        module._registrar_relacion_familiar_importacion(
            cid_resp=10,
            cid_beneficiario=20,
            offset=9,
            relaciones_familiares_pairs=pares,
            relaciones_familiares=relaciones,
        )
        is True
    )
    assert (
        module._registrar_relacion_familiar_importacion(
            cid_resp=10,
            cid_beneficiario=20,
            offset=9,
            relaciones_familiares_pairs=pares,
            relaciones_familiares=relaciones,
        )
        is False
    )

    assert relaciones == [{"hijo_id": 20, "responsable_id": 10, "fila": 9}]


def test_importacion_helpers_resuelve_localidad_responsable_con_parentesis(mocker):
    class _LocalidadesQS:
        def filter(self, **kwargs):
            if "municipio__provincia_id" in kwargs:
                return self
            if kwargs == {"nombre__iexact": "Rosario"}:
                return [SimpleNamespace(pk=44, municipio=SimpleNamespace(pk=55))]
            return []

    mocker.patch(
        "celiaquia.services.importacion_service.Localidad.objects.select_related",
        return_value=_LocalidadesQS(),
    )

    responsable_payload = {}
    payload = {"localidad_responsable": "Rosario (Municipio Rosario)"}
    module._resolver_localidad_responsable_payload_importacion(
        responsable_payload=responsable_payload,
        payload=payload,
        provincia_usuario_id=7,
        offset=1,
        add_warning=lambda *_args, **_kwargs: None,
    )

    assert responsable_payload["localidad"] == 44
    assert responsable_payload["municipio"] == 55


def test_importacion_helpers_crear_responsable_y_legajo(mocker):
    warnings = []

    def _add_warning(fila, campo, detalle):
        warnings.append((fila, campo, detalle))

    class _FakeExpedienteCiudadano:
        ROLE_RESPONSABLE = "RESP"

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    mocker.patch.object(module, "ExpedienteCiudadano", _FakeExpedienteCiudadano)

    legajos_crear = []
    existentes_ids = set()
    fake_ciudadano = SimpleNamespace(pk=55)

    cid_resp, legajo_agregado = module._crear_responsable_y_legajo_importacion(
        responsable_payload={"fecha_nacimiento": date(1980, 1, 1)},
        payload_beneficiario={"fecha_nacimiento": date(2010, 1, 1)},
        usuario=SimpleNamespace(id=1),
        expediente=SimpleNamespace(id=99),
        estado_id=4,
        existentes_ids=existentes_ids,
        legajos_crear=legajos_crear,
        offset=7,
        add_warning=_add_warning,
        validar_edad_responsable_fn=lambda *_a, **_k: (
            False,
            ["warning edad"],
            "error edad",
        ),
        get_or_create_ciudadano=lambda **_kwargs: fake_ciudadano,
    )

    assert cid_resp == 55
    assert legajo_agregado is True
    assert existentes_ids == {55}
    assert len(legajos_crear) == 1
    assert legajos_crear[0].kwargs["rol"] == "RESP"
    assert warnings == []


def test_importacion_helpers_conflictos_beneficiario_y_exclusion():
    ciudadano = SimpleNamespace(
        pk=101,
        documento="12345678",
        nombre="Ana",
        apellido="Perez",
    )
    excluidos = []

    assert (
        module._beneficiario_tiene_conflicto_importacion(
            ciudadano=ciudadano,
            offset=4,
            existentes_ids={101},
            en_programa={},
            abiertos={},
            excluidos=excluidos,
        )
        is True
    )
    assert excluidos[0]["motivo"] == "Ya existe en este expediente"

    excluidos_2 = []
    assert (
        module._beneficiario_tiene_conflicto_importacion(
            ciudadano=ciudadano,
            offset=5,
            existentes_ids=set(),
            en_programa={101: {"es_titular_activo": False, "expediente_id": 88}},
            abiertos={},
            excluidos=excluidos_2,
        )
        is True
    )
    assert excluidos_2[0]["estado_programa"] == "SUSPENDIDO"

    excluidos_3 = []
    assert (
        module._beneficiario_tiene_conflicto_importacion(
            ciudadano=ciudadano,
            offset=6,
            existentes_ids=set(),
            en_programa={},
            abiertos={},
            excluidos=excluidos_3,
        )
        is False
    )
    assert excluidos_3 == []


def test_importacion_helpers_registrar_legajo_beneficiario(mocker):
    class _FakeExpedienteCiudadano:
        ROLE_BENEFICIARIO = "BEN"

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    mocker.patch.object(module, "ExpedienteCiudadano", _FakeExpedienteCiudadano)
    ciudadano = SimpleNamespace(pk=33)
    expediente = SimpleNamespace(id=9, estado=SimpleNamespace(nombre="CREADO"))
    legajos_crear = []
    existentes_ids = set()
    abiertos = {}

    cid = module._registrar_legajo_beneficiario_importacion(
        ciudadano=ciudadano,
        expediente=expediente,
        estado_id=5,
        existentes_ids=existentes_ids,
        abiertos=abiertos,
        legajos_crear=legajos_crear,
    )

    assert cid == 33
    assert existentes_ids == {33}
    assert len(legajos_crear) == 1
    assert legajos_crear[0].kwargs["rol"] == "BEN"
    assert abiertos[33]["expediente__estado__nombre"] == "CREADO"
    assert abiertos[33]["estado_cupo"] == module.EstadoCupo.NO_EVAL


def test_importacion_helpers_crear_ciudadano_beneficiario_registra_errores():
    payload = {"nombre": "Ana", "documento": "123", "email": None}
    detalles_errores = []
    usuario = SimpleNamespace(id=1)
    expediente = SimpleNamespace(id=2)

    ciudadano_ok = module._crear_ciudadano_beneficiario_importacion(
        payload=payload,
        usuario=usuario,
        expediente=expediente,
        offset=2,
        detalles_errores=detalles_errores,
        get_or_create_ciudadano=lambda **_kwargs: SimpleNamespace(pk=99),
    )
    assert ciudadano_ok.pk == 99
    assert detalles_errores == []

    ciudadano_none = module._crear_ciudadano_beneficiario_importacion(
        payload=payload,
        usuario=usuario,
        expediente=expediente,
        offset=3,
        detalles_errores=detalles_errores,
        get_or_create_ciudadano=lambda **_kwargs: SimpleNamespace(pk=None),
    )
    assert ciudadano_none is None
    assert detalles_errores[-1]["fila"] == 3
    assert detalles_errores[-1]["error"] == "No se pudo crear el ciudadano"
    assert detalles_errores[-1]["datos"] == {"nombre": "Ana", "documento": "123"}

    ciudadano_exc = module._crear_ciudadano_beneficiario_importacion(
        payload=payload,
        usuario=usuario,
        expediente=expediente,
        offset=4,
        detalles_errores=detalles_errores,
        get_or_create_ciudadano=lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("boom")
        ),
    )
    assert ciudadano_exc is None
    assert detalles_errores[-1]["fila"] == 4
    assert "Error creando ciudadano: boom" == detalles_errores[-1]["error"]


def test_importacion_helpers_orquesta_beneficiario_y_detecta_responsable(mocker):
    fake_ciudadano = SimpleNamespace(pk=77)
    crear_mock = mocker.patch.object(
        module,
        "_crear_ciudadano_beneficiario_importacion",
        return_value=None,
    )
    conflicto_mock = mocker.patch.object(
        module,
        "_beneficiario_tiene_conflicto_importacion",
        return_value=False,
    )
    registrar_mock = mocker.patch.object(
        module,
        "_registrar_legajo_beneficiario_importacion",
        return_value=77,
    )

    status, cid = module._procesar_beneficiario_importacion(
        payload={"nombre": "Ana"},
        usuario=SimpleNamespace(id=1),
        expediente=SimpleNamespace(id=2),
        estado_id=5,
        offset=2,
        detalles_errores=[],
        existentes_ids=set(),
        en_programa={},
        abiertos={},
        excluidos=[],
        legajos_crear=[],
        get_or_create_ciudadano=lambda **_kwargs: fake_ciudadano,
    )
    assert (status, cid) == ("error", None)
    conflicto_mock.assert_not_called()
    registrar_mock.assert_not_called()

    crear_mock.return_value = fake_ciudadano
    conflicto_mock.return_value = True
    status, cid = module._procesar_beneficiario_importacion(
        payload={"nombre": "Ana"},
        usuario=SimpleNamespace(id=1),
        expediente=SimpleNamespace(id=2),
        estado_id=5,
        offset=3,
        detalles_errores=[],
        existentes_ids=set(),
        en_programa={},
        abiertos={},
        excluidos=[],
        legajos_crear=[],
        get_or_create_ciudadano=lambda **_kwargs: fake_ciudadano,
    )
    assert (status, cid) == ("excluido", None)
    registrar_mock.assert_not_called()

    conflicto_mock.return_value = False
    registrar_mock.return_value = 77
    status, cid = module._procesar_beneficiario_importacion(
        payload={"nombre": "Ana"},
        usuario=SimpleNamespace(id=1),
        expediente=SimpleNamespace(id=2),
        estado_id=5,
        offset=4,
        detalles_errores=[],
        existentes_ids=set(),
        en_programa={},
        abiertos={},
        excluidos=[],
        legajos_crear=[],
        get_or_create_ciudadano=lambda **_kwargs: fake_ciudadano,
    )
    assert (status, cid) == ("ok", 77)
    assert registrar_mock.call_count == 1

    assert module._tiene_datos_responsable_importacion({}) is False
    assert (
        module._tiene_datos_responsable_importacion({"nombre_responsable": "Ana"})
        is True
    )


def test_importacion_helpers_procesar_responsable_same_document():
    warnings = []

    def _add_warning(fila, campo, detalle):
        warnings.append((fila, campo, detalle))

    def _add_error(_fila, _campo, detalle):
        raise ValidationError(detalle)

    payload = {
        "apellido_responsable": "Perez",
        "nombre_responsable": "Ana",
        "documento_responsable": "20123456783",
        "documento": "20123456783",
        "sexo_responsable": "F",
    }

    relaciones = []
    pares = set()
    legajos = []
    existentes_ids = set()

    cid_resp, legajo_agregado, relacion_agregada = (
        module._procesar_responsable_importacion(
            payload=payload,
            cid_beneficiario=77,
            usuario=SimpleNamespace(id=1),
            expediente=SimpleNamespace(id=9),
            estado_id=5,
            provincia_usuario_id=7,
            offset=12,
            normalizar_sexo=lambda value: 2 if value == "F" else None,
            to_date=lambda value: value,
            add_warning=_add_warning,
            add_error=_add_error,
            validar_edad_responsable_fn=lambda *_a, **_k: (True, [], None),
            existentes_ids=existentes_ids,
            legajos_crear=legajos,
            relaciones_familiares_pairs=pares,
            relaciones_familiares=relaciones,
            get_or_create_ciudadano=lambda **_kwargs: (_ for _ in ()).throw(
                AssertionError("No debería crear ciudadano si es mismo documento")
            ),
            responsable_payload={"documento": "20123456783"},
        )
    )

    assert (cid_resp, legajo_agregado, relacion_agregada) == (77, False, False)
    assert relaciones == []
    assert pares == set()
    assert legajos == []
    assert warnings == [
        (
            12,
            "responsable",
            "Responsable es el mismo beneficiario - no se duplica legajo",
        )
    ]


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


def test_preview_excel_uses_xlsx_reader_and_normalizes_datetime(mocker):
    f = _DummyFile(b"fake-xlsx", name="datos.xlsx")

    mocker.patch(
        "celiaquia.services.importacion_service.pd.read_excel",
        return_value=pd.DataFrame(
            {
                "Fecha Nacimiento": [pd.Timestamp("2020-01-01")],
                "Nombre": ["Ana"],
            }
        ),
    )

    out = module.ImportacionService.preview_excel(f)
    assert out["headers"] == ["ID", "fecha_nacimiento", "nombre"]
    assert out["rows"][0]["ID"] == 1
    assert str(out["rows"][0]["fecha_nacimiento"]) == "2020-01-01"


def test_importar_legajos_guarda_registros_erroneos_y_sin_bulk_legajos(mocker):
    class _FakeQs:
        def select_related(self, *_a, **_k):
            return self

        def exclude(self, *_a, **_k):
            return self

        def filter(self, *_a, **_k):
            return self

        def values(self, *_a, **_k):
            return []

        def values_list(self, *_a, **_k):
            return []

        def first(self):
            return None

        def __iter__(self):
            return iter([])

    fake_qs = _FakeQs()
    bulk_legajos = mocker.Mock()
    fake_manager = SimpleNamespace(
        filter=lambda *_a, **_k: fake_qs,
        select_related=lambda *_a, **_k: fake_qs,
        bulk_create=bulk_legajos,
    )
    mocker.patch.object(module.ExpedienteCiudadano, "objects", fake_manager)

    registros_guardados = mocker.Mock()

    class _RegistroErroneo:
        objects = SimpleNamespace(bulk_create=registros_guardados)

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    mocker.patch("celiaquia.models.RegistroErroneo", _RegistroErroneo)
    mocker.patch(
        "celiaquia.services.importacion_service._estado_doc_pendiente_id",
        return_value=9,
    )
    mocker.patch(
        "celiaquia.services.importacion_service.pd.read_excel",
        return_value=pd.DataFrame(
            [
                {
                    "nombre": "Juan",
                    "documento": "1234567890",
                    "fecha_nacimiento": "2000-01-01",
                }
            ]
        ),
    )
    mocker.patch(
        "celiaquia.services.importacion_service.Sexo.objects.all", return_value=[]
    )

    class _UserBrokenProfile:
        @property
        def profile(self):
            raise RuntimeError("sin profile")

    expediente = SimpleNamespace(id=55, estado=SimpleNamespace(nombre="CREADO"))
    archivo = _DummyFile(b"excel", name="data.xlsx")

    result = module.ImportacionService.importar_legajos_desde_excel(
        expediente,
        archivo,
        _UserBrokenProfile(),
        batch_size=25,
    )

    assert result["validos"] == 0
    assert result["errores"] == 1
    assert len(result["detalles_errores"]) == 1
    assert "Faltan campos obligatorios" in result["detalles_errores"][0]["error"]
    bulk_legajos.assert_not_called()
    registros_guardados.assert_called_once()


def test_importacion_helpers_persistir_legajos_y_guardar_registros_erroneos(mocker):
    crear_relaciones = mocker.patch.object(
        module, "_crear_relaciones_familiares_importacion"
    )
    bulk_create = mocker.patch(
        "celiaquia.services.importacion_service.ExpedienteCiudadano.objects.bulk_create"
    )

    module._persistir_legajos_importacion(
        legajos_crear=[SimpleNamespace(pk=1), SimpleNamespace(pk=2)],
        batch_size=50,
        relaciones_familiares=[{"fila": 3, "responsable_id": 1, "hijo_id": 2}],
        warnings=[],
    )
    bulk_create.assert_called_once()
    crear_relaciones.assert_called_once()

    expediente = _crear_expediente_test()
    module._guardar_registros_erroneos_importacion(
        expediente=expediente,
        detalles_errores=[
            {
                "fila": 7,
                "datos": {
                    "fecha_nacimiento": date(2020, 1, 2),
                    "timestamp": pd.Timestamp("2020-03-04 10:30:00"),
                    "nombre": "Ana",
                },
                "error": "Documento invÃ¡lido",
            }
        ],
        batch_size=10,
    )

    reg = RegistroErroneo.objects.get(expediente=expediente)
    assert reg.fila_excel == 7
    assert reg.mensaje_error == "Documento invÃ¡lido"
    assert reg.datos_raw["fecha_nacimiento"] == "02/01/2020"
    assert reg.datos_raw["timestamp"] == "04/03/2020"
    assert reg.datos_raw["nombre"] == "Ana"


def test_importacion_helpers_consolidar_roles_cruzados_noop_y_error(mocker):
    expediente = _crear_expediente_test()
    estado_legajo = _crear_estado_legajo_test()
    ciudadano = _crear_ciudadano_test(30111222)

    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )
    out = module._consolidar_roles_cruzados_importacion(expediente, warnings := [])
    assert out == 0
    legajo.refresh_from_db()
    assert legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO
    assert warnings == []

    err_logger = mocker.patch("celiaquia.services.importacion_service.logger.error")

    class _FailingLegajosQS:
        def select_related(self, *_a, **_k):
            raise RuntimeError("boom relaciones cruzadas")

    mocker.patch(
        "celiaquia.services.importacion_service.ExpedienteCiudadano.objects.filter",
        return_value=_FailingLegajosQS(),
    )

    warnings_error = []
    out_err = module._consolidar_roles_cruzados_importacion(expediente, warnings_error)
    assert out_err == 0
    assert warnings_error == [
        {
            "fila": "general",
            "campo": "relaciones_cruzadas",
            "detalle": "Error procesando relaciones cruzadas: boom relaciones cruzadas",
        }
    ]
    assert err_logger.called


def test_importacion_helpers_consolidar_roles_cruzados_actualiza_y_elimina_mockeado():
    class _Legajo:
        def __init__(self, ciudadano_id, rol):
            self.ciudadano_id = ciudadano_id
            self.rol = rol
            self.saved = []
            self.hard_deleted = False

        def save(self, update_fields=None):
            self.saved.append(update_fields)

        def hard_delete(self):
            self.hard_deleted = True

    leg_ben = _Legajo(10, module.ExpedienteCiudadano.ROLE_BENEFICIARIO)
    leg_resp = _Legajo(10, module.ExpedienteCiudadano.ROLE_RESPONSABLE)

    class _FakeLegajosQS:
        def __init__(self, items):
            self.items = items

        def select_related(self, *_a, **_k):
            return self

        def filter(self, **kwargs):
            filtered = self.items
            for key, value in kwargs.items():
                filtered = [x for x in filtered if getattr(x, key) == value]
            return _FakeLegajosQS(filtered)

        def values_list(self, field_name, flat=False):
            assert field_name == "ciudadano_id"
            assert flat is True
            return [getattr(x, field_name) for x in self.items]

        def first(self):
            return self.items[0] if self.items else None

    original_filter = module.ExpedienteCiudadano.objects.filter
    try:
        module.ExpedienteCiudadano.objects.filter = lambda **_kwargs: _FakeLegajosQS(
            [leg_ben, leg_resp]
        )
        out = module._consolidar_roles_cruzados_importacion(
            SimpleNamespace(id=77), warnings=[]
        )
    finally:
        module.ExpedienteCiudadano.objects.filter = original_filter

    assert out == 1
    assert leg_ben.rol == module.ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE
    assert leg_ben.saved == [["rol"]]
    assert leg_resp.hard_deleted is True


def test_importacion_helpers_crear_relaciones_familiares_db_real():
    c1 = _crear_ciudadano_test(40111222)
    c2 = _crear_ciudadano_test(40111223)

    warnings = []
    module._crear_relaciones_familiares_importacion(
        relaciones_familiares=[
            {"fila": 2, "responsable_id": c1.id, "hijo_id": c2.id},
            # Duplicado para caracterizar idempotencia vÃ­a get_or_create
            {"fila": 2, "responsable_id": c1.id, "hijo_id": c2.id},
        ],
        warnings=warnings,
    )

    rel = GrupoFamiliar.objects.get(ciudadano_1_id=c1.id, ciudadano_2_id=c2.id)
    assert rel.vinculo == GrupoFamiliar.RELACION_PADRE
    assert rel.estado_relacion == GrupoFamiliar.ESTADO_BUENO
    assert rel.conviven is True
    assert rel.cuidador_principal is True
    assert (
        GrupoFamiliar.objects.filter(ciudadano_1_id=c1.id, ciudadano_2_id=c2.id).count()
        == 1
    )
    assert warnings == []


def test_importar_legajos_acumula_warnings_emitidos_por_callbacks(mocker):
    df = pd.DataFrame([{"documento": "111"}])
    mocker.patch(
        "celiaquia.services.importacion_service._leer_excel_importacion",
        return_value=df,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._normalizar_dataframe_importacion",
        side_effect=lambda x: x,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._estado_doc_pendiente_id",
        return_value=9,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._obtener_provincia_usuario_id",
        return_value=7,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._precargar_datos_importacion",
        return_value={
            "municipios_cache": {},
            "localidades_cache": {},
            "sexos_cache": {},
            "nacionalidades_nombres": set(),
            "sexos_nombres": set(),
        },
    )

    def _build_payload_side_effect(**kwargs):
        kwargs["add_warning"](kwargs["offset"], "documento", "Documento normalizado")
        return {"documento": "111"}

    mocker.patch(
        "celiaquia.services.importacion_service._construir_payload_fila_importacion",
        side_effect=_build_payload_side_effect,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._procesar_beneficiario_importacion",
        return_value=("excluido", None),
    )
    mocker.patch(
        "celiaquia.services.importacion_service._tiene_datos_responsable_importacion",
        return_value=False,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._persistir_legajos_importacion"
    )
    mocker.patch(
        "celiaquia.services.importacion_service._guardar_registros_erroneos_importacion"
    )
    mocker.patch(
        "celiaquia.services.importacion_service._consolidar_roles_cruzados_importacion",
        return_value=0,
    )

    class _ExistingQS:
        def values_list(self, *_a, **_k):
            return []

    class _ConflictosQS:
        def exclude(self, *_a, **_k):
            return self

        def filter(self, *_a, **_k):
            return self

        def values(self, *_a, **_k):
            return []

    mocker.patch.object(
        module.ExpedienteCiudadano,
        "objects",
        SimpleNamespace(
            filter=lambda *_a, **_k: _ExistingQS(),
            select_related=lambda *_a, **_k: _ConflictosQS(),
        ),
    )

    result = module.ImportacionService.importar_legajos_desde_excel(
        expediente=SimpleNamespace(id=99, estado=SimpleNamespace(nombre="CREADO")),
        archivo_excel=_DummyFile(b"fake", name="warn.xlsx"),
        usuario=SimpleNamespace(id=1),
    )

    assert result["warnings"] == [
        {"fila": 2, "campo": "documento", "detalle": "Documento normalizado"}
    ]
    assert result["excluidos_count"] == 0


def test_importar_legajos_orquesta_loop_principal_y_postprocesos(mocker):
    df = pd.DataFrame(
        [
            {"documento": "111"},
            {"documento": "222"},
            {"documento": "333"},
            {"documento": "444"},
        ]
    )

    mocker.patch(
        "celiaquia.services.importacion_service._leer_excel_importacion",
        return_value=df,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._normalizar_dataframe_importacion",
        side_effect=lambda x: x,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._estado_doc_pendiente_id",
        return_value=9,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._obtener_provincia_usuario_id",
        return_value=7,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._precargar_datos_importacion",
        return_value={
            "municipios_cache": {},
            "localidades_cache": {},
            "sexos_cache": {},
            "nacionalidades_nombres": set(),
            "sexos_nombres": set(),
        },
    )
    mocker.patch(
        "celiaquia.services.importacion_service._build_datos_originales_error_importacion",
        side_effect=lambda row: {"documento": row.get("documento")},
    )

    payloads = [
        {"documento": "111", "tiene_resp": True},
        {"documento": "222", "tiene_resp": False},
        {"documento": "333", "tiene_resp": False},
        ValidationError("Fila invÃ¡lida"),
    ]
    construir_payload = mocker.patch(
        "celiaquia.services.importacion_service._construir_payload_fila_importacion",
        side_effect=payloads,
    )

    def _procesar_beneficiario_side_effect(**kwargs):
        payload = kwargs["payload"]
        if payload["documento"] == "111":
            kwargs["legajos_crear"].append(SimpleNamespace(pk=101))
            return "ok", 101
        if payload["documento"] == "222":
            kwargs["excluidos"].append({"fila": kwargs["offset"], "cid": 202})
            return "excluido", None
        kwargs["detalles_errores"].append(
            {"fila": kwargs["offset"], "error": "Error beneficiario", "datos": payload}
        )
        return "error", None

    procesar_benef = mocker.patch(
        "celiaquia.services.importacion_service._procesar_beneficiario_importacion",
        side_effect=_procesar_beneficiario_side_effect,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._tiene_datos_responsable_importacion",
        side_effect=lambda payload: bool(payload.get("tiene_resp")),
    )
    mocker.patch(
        "celiaquia.services.importacion_service._validar_y_normalizar_responsable_payload_importacion",
        return_value=({"documento": "999"}, False),
    )

    def _procesar_responsable_side_effect(**kwargs):
        kwargs["relaciones_familiares"].append(
            {
                "fila": kwargs["offset"],
                "responsable_id": 1000,
                "hijo_id": kwargs["cid_beneficiario"],
            }
        )
        return 1000, True, True

    procesar_resp = mocker.patch(
        "celiaquia.services.importacion_service._procesar_responsable_importacion",
        side_effect=_procesar_responsable_side_effect,
    )
    persistir = mocker.patch(
        "celiaquia.services.importacion_service._persistir_legajos_importacion"
    )
    guardar_err = mocker.patch(
        "celiaquia.services.importacion_service._guardar_registros_erroneos_importacion"
    )
    consolidar = mocker.patch(
        "celiaquia.services.importacion_service._consolidar_roles_cruzados_importacion",
        return_value=2,
    )

    class _ExistingQS:
        def values_list(self, *_a, **_k):
            return []

    class _ConflictosQS:
        def exclude(self, *_a, **_k):
            return self

        def filter(self, *_a, **_k):
            return self

        def values(self, *_a, **_k):
            return []

    fake_manager = SimpleNamespace(
        filter=lambda *_a, **_k: _ExistingQS(),
        select_related=lambda *_a, **_k: _ConflictosQS(),
    )
    mocker.patch.object(module.ExpedienteCiudadano, "objects", fake_manager)

    expediente = SimpleNamespace(id=77, estado=SimpleNamespace(nombre="CREADO"))
    usuario = SimpleNamespace(id=10)
    archivo = _DummyFile(b"fake-xlsx", name="lote.xlsx")

    result = module.ImportacionService.importar_legajos_desde_excel(
        expediente,
        archivo,
        usuario,
        batch_size=25,
    )

    assert result["validos"] == 1
    assert result["errores"] == 2  # helper error + excepciÃ³n de fila
    assert result["excluidos_count"] == 1
    assert result["relaciones_familiares_creadas"] == 1
    assert result["relaciones_cruzadas_consolidadas"] == 2
    assert len(result["detalles_errores"]) == 2
    assert any("Fila invÃ¡lida" in d["error"] for d in result["detalles_errores"])
    assert construir_payload.call_count == 4
    assert procesar_benef.call_count == 3
    procesar_resp.assert_called_once()
    persistir.assert_called_once()
    guardar_err.assert_called_once()
    consolidar.assert_called_once()

    kwargs_persistir = persistir.call_args.kwargs
    assert kwargs_persistir["batch_size"] == 25
    assert len(kwargs_persistir["legajos_crear"]) == 1
    assert len(kwargs_persistir["relaciones_familiares"]) == 1


def test_importar_legajos_registra_error_si_falla_responsable_tras_beneficiario(mocker):
    df = pd.DataFrame([{"documento": "111"}])
    mocker.patch(
        "celiaquia.services.importacion_service._leer_excel_importacion",
        return_value=df,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._normalizar_dataframe_importacion",
        side_effect=lambda x: x,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._estado_doc_pendiente_id",
        return_value=9,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._obtener_provincia_usuario_id",
        return_value=7,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._precargar_datos_importacion",
        return_value={
            "municipios_cache": {},
            "localidades_cache": {},
            "sexos_cache": {},
            "nacionalidades_nombres": set(),
            "sexos_nombres": set(),
        },
    )

    def _procesar_beneficiario_ok(**kwargs):
        kwargs["legajos_crear"].append(SimpleNamespace(pk=501))
        kwargs["existentes_ids"].add(501)
        kwargs["abiertos"][501] = {"expediente_id": 88}
        return {"documento": "111"}, {"documento": "222"}, False, "ok", 501

    mocker.patch(
        "celiaquia.services.importacion_service._procesar_beneficiario_desde_row_importacion",
        side_effect=_procesar_beneficiario_ok,
    )
    mocker.patch(
        "celiaquia.services.importacion_service._procesar_responsable_si_corresponde_importacion",
        side_effect=ValidationError("Responsable inválido"),
    )
    mocker.patch(
        "celiaquia.services.importacion_service._build_datos_originales_error_importacion",
        return_value={"documento": "111"},
    )
    persistir = mocker.patch(
        "celiaquia.services.importacion_service._persistir_legajos_importacion"
    )
    guardar_err = mocker.patch(
        "celiaquia.services.importacion_service._guardar_registros_erroneos_importacion"
    )
    mocker.patch(
        "celiaquia.services.importacion_service._consolidar_roles_cruzados_importacion",
        return_value=0,
    )

    class _ExistingQS:
        def values_list(self, *_a, **_k):
            return []

    class _ConflictosQS:
        def exclude(self, *_a, **_k):
            return self

        def filter(self, *_a, **_k):
            return self

        def values(self, *_a, **_k):
            return []

    mocker.patch.object(
        module.ExpedienteCiudadano,
        "objects",
        SimpleNamespace(
            filter=lambda *_a, **_k: _ExistingQS(),
            select_related=lambda *_a, **_k: _ConflictosQS(),
        ),
    )

    result = module.ImportacionService.importar_legajos_desde_excel(
        expediente=SimpleNamespace(id=88, estado=SimpleNamespace(nombre="CREADO")),
        archivo_excel=_DummyFile(b"fake", name="lote.xlsx"),
        usuario=SimpleNamespace(id=1),
        batch_size=20,
    )

    assert result["validos"] == 0
    assert result["errores"] == 1
    assert result["relaciones_familiares_creadas"] == 0
    assert result["detalles_errores"] == [
        {"fila": 2, "error": "['Responsable inválido']", "datos": {"documento": "111"}}
    ]
    persistir.assert_called_once()
    assert persistir.call_args.kwargs["legajos_crear"] == []
    guardar_err.assert_called_once()
