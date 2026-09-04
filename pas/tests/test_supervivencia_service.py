from datetime import date
from unittest.mock import call, patch

import pytest

from core.models import Municipio, Provincia
from pas.models import (
    PasControlRenaper,
    PasEstado,
    PasIncompatibilidad,
    PasPersona,
)
from pas.services.supervivencia_service import sincronizar_supervivencia_pas


@pytest.fixture
def persona_supervivencia(db):
    provincia = Provincia.objects.create(nombre="Provincia control RENAPER")
    municipio = Municipio.objects.create(
        nombre="Municipio control RENAPER",
        provincia=provincia,
    )
    estado, _ = PasEstado.objects.get_or_create(nombre="Activo")
    return PasPersona.objects.create(
        id_persona=870001,
        apellidos="Control",
        nombres="Renaper",
        dni=30123456,
        cuit="20301234561",
        provincia=provincia,
        municipio=municipio,
        estado=estado,
    )


@pytest.mark.django_db
def test_fallecimiento_crea_incompatibilidad_para_mes_siguiente(
    persona_supervivencia,
):
    with patch(
        "pas.services.supervivencia_service.consultar_datos_renaper",
        return_value={
            "success": False,
            "error_type": "fallecido",
            "fallecido": True,
        },
    ):
        resumen = sincronizar_supervivencia_pas(
            fecha_consulta=date(2026, 7, 29),
        )

    control = PasControlRenaper.objects.get(persona=persona_supervivencia)
    incompatibilidad = PasIncompatibilidad.objects.get(persona=persona_supervivencia)
    assert control.resultado == PasControlRenaper.Resultado.FALLECIDA
    assert incompatibilidad.categoria == PasIncompatibilidad.Categoria.SUPERVIVENCIA
    assert incompatibilidad.periodo_impacto == date(2026, 8, 1)
    assert incompatibilidad.estado == PasIncompatibilidad.Estado.PENDIENTE
    assert resumen["fallecidas"] == 1


@pytest.mark.django_db
def test_persona_viva_no_crea_incompatibilidad(persona_supervivencia):
    with patch(
        "pas.services.supervivencia_service.consultar_datos_renaper",
        return_value={"success": True, "data": {}},
    ):
        resumen = sincronizar_supervivencia_pas(
            fecha_consulta=date(2026, 7, 29),
        )

    assert PasControlRenaper.objects.get().resultado == "vigente"
    assert not PasIncompatibilidad.objects.exists()
    assert resumen["vigentes"] == 1


@pytest.mark.django_db
def test_sin_sexo_prueba_m_y_f_solo_ante_no_match(persona_supervivencia):
    with patch(
        "pas.services.supervivencia_service.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error_type": "no_match"},
            {"success": True, "data": {}},
        ],
    ) as consultar:
        sincronizar_supervivencia_pas(fecha_consulta=date(2026, 7, 29))

    assert consultar.call_args_list == [
        call(str(persona_supervivencia.dni), "M"),
        call(str(persona_supervivencia.dni), "F"),
    ]
    assert PasControlRenaper.objects.get().sexo_consulta == "F"


@pytest.mark.django_db
def test_control_diario_es_idempotente(persona_supervivencia):
    with patch(
        "pas.services.supervivencia_service.consultar_datos_renaper",
        return_value={"success": True, "data": {}},
    ) as consultar:
        sincronizar_supervivencia_pas(fecha_consulta=date(2026, 7, 29))
        segundo_resumen = sincronizar_supervivencia_pas(
            fecha_consulta=date(2026, 7, 29)
        )

    assert consultar.call_count == 1
    assert PasControlRenaper.objects.count() == 1
    assert segundo_resumen["omitidas"] == 1
