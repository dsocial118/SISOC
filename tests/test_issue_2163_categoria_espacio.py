"""Regresiones para la categorización de espacios comunitarios (#2163)."""

import json

import pytest
from django.core.exceptions import ValidationError

from comedores.forms.comedor_form import ComedorForm
from comedores.models import Comedor, EstadoActividad, EstadoProceso
from comedores.services.comedor_service import ComedorService
from comedores.services.filter_config import FIELD_TYPES, get_filters_ui_config
from core.models import Provincia


def test_categoria_espacio_comunitario_es_opcional_y_otra_requiere_detalle():
    comedor = Comedor(
        nombre="Espacio barrial",
        categoria_espacio_comunitario=Comedor.CATEGORIA_ESPACIO_OTRA,
    )

    with pytest.raises(ValidationError, match="Especifique la otra categoría"):
        comedor.full_clean(exclude={"provincia"})

    comedor.categoria_espacio_comunitario_otra = "Mutual vecinal"
    comedor.full_clean(exclude={"provincia"})


def test_filtro_avanzado_expone_categoria_de_espacio_comunitario():
    config = get_filters_ui_config()

    categoria = next(
        field
        for field in config["fields"]
        if field["name"] == "categoria_espacio_comunitario"
    )

    assert categoria["type"] == "choice"
    assert FIELD_TYPES["categoria_espacio_comunitario"] == "choice"
    assert {choice["value"] for choice in categoria["choices"]} == {
        value for value, _label in Comedor.CATEGORIAS_ESPACIO_COMUNITARIO
    }


def test_formulario_limpia_detalle_de_otra_categoria_que_ya_no_aplica(db):
    provincia = Provincia.objects.create(nombre="Chaco")
    actividad = EstadoActividad.objects.create(estado="Activo")
    proceso = EstadoProceso.objects.create(
        estado="En seguimiento", estado_actividad=actividad
    )

    form = ComedorForm(
        data={
            "nombre": "Espacio barrial",
            "provincia": str(provincia.pk),
            "estado_general": str(actividad.pk),
            "subestado": str(proceso.pk),
            "motivo": "",
            "categoria_espacio_comunitario": Comedor.CATEGORIA_ESPACIO_HOGAR,
            "categoria_espacio_comunitario_otra": "Dato obsoleto",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["categoria_espacio_comunitario_otra"] == ""


def test_filtro_avanzado_filtra_por_categoria_de_espacio_comunitario(db):
    provincia = Provincia.objects.create(nombre="Chaco")
    comedor_match = Comedor.objects.create(
        nombre="Club barrial",
        provincia=provincia,
        categoria_espacio_comunitario=Comedor.CATEGORIA_ESPACIO_CLUB_SOCIAL_DEPORTIVO,
    )
    Comedor.objects.create(
        nombre="Hogar comunitario",
        provincia=provincia,
        categoria_espacio_comunitario=Comedor.CATEGORIA_ESPACIO_HOGAR,
    )
    filters = json.dumps(
        {
            "logic": "AND",
            "items": [
                {
                    "field": "categoria_espacio_comunitario",
                    "op": "eq",
                    "value": Comedor.CATEGORIA_ESPACIO_CLUB_SOCIAL_DEPORTIVO,
                }
            ],
        }
    )

    rows = list(ComedorService.get_filtered_comedores({"filters": filters}))

    assert [row["id"] for row in rows] == [comedor_match.id]
