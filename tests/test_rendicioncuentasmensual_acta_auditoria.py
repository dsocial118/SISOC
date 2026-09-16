from pathlib import Path
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from rendicioncuentasmensual.forms import RendicionProcesoForm
from rendicioncuentasmensual.models import RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from rendicioncuentasmensual.services import RendicionProcesoService
from organizaciones.models import Organizacion, ProyectoOrganizacion


@pytest.fixture
def tmp_path():
    """Evita crear temporales de pytest fuera del sandbox del worktree."""
    return Path.cwd()


@pytest.fixture(autouse=True)
def almacenamiento_en_memoria(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    }


def _crear_proyecto(codigo):
    organizacion = Organizacion.objects.create(nombre=f"Organización {codigo}")
    return ProyectoOrganizacion.objects.create(
        organizacion=organizacion,
        codigo=codigo,
        nombre=f"Proyecto {codigo}",
    )


def _crear_rendicion(*, proyecto=None, **overrides):
    datos = {
        "mes": 9,
        "anio": 2026,
        "proyecto": proyecto,
        "convenio": "P01",
        "numero_rendicion": 1,
        "periodo_inicio": date(2026, 9, 1),
        "periodo_fin": date(2026, 9, 30),
        "linea_programatica": RendicionCuentaMensual.LINEA_TRADICIONAL,
        "etapa_proceso": RendicionCuentaMensual.ETAPA_AUDITORIA,
        "subestado_proceso": RendicionCuentaMensual.SUBESTADO_EN_CURSO,
    }
    datos.update(overrides)
    return RendicionCuentaMensual.objects.create(**datos)


@pytest.mark.django_db
def test_linea_secos_finaliza_sin_acta_ni_selector_si_no():
    rendicion = RendicionCuentaMensual.objects.create(
        mes=9,
        anio=2026,
        linea_programatica=RendicionCuentaMensual.LINEA_SECOS,
        etapa_proceso=RendicionCuentaMensual.ETAPA_AUDITORIA,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_EN_CURSO,
    )
    form = RendicionProcesoForm(
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "100.00",
        },
        rendicion=rendicion,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["genera_acta_auditoria"] is None


@pytest.mark.django_db
def test_rendiciones_elegibles_para_acta_aplica_todo_el_scope_confirmado():
    proyecto = _crear_proyecto("PROY-01")
    otro_proyecto = _crear_proyecto("PROY-02")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=6)
    elegible = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )
    _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=2,
        genera_acta_auditoria=True,
    )
    _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=3,
        genera_acta_auditoria=None,
    )
    _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=4,
        linea_programatica=RendicionCuentaMensual.LINEA_SECOS,
        genera_acta_auditoria=False,
    )
    _crear_rendicion(
        proyecto=otro_proyecto,
        numero_rendicion=5,
        genera_acta_auditoria=False,
    )

    resultado = RendicionCuentaMensualService.rendiciones_elegibles_para_acta(rendicion)

    assert list(resultado) == [elegible]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "linea_programatica",
    [
        RendicionCuentaMensual.LINEA_SECOS,
        RendicionCuentaMensual.LINEA_TRADICIONAL,
    ],
)
def test_acta_es_opcional_al_finalizar_para_todos_los_programas(
    linea_programatica,
):
    rendicion = _crear_rendicion(linea_programatica=linea_programatica)
    datos = {"monto_rendido": Decimal("100.00")}
    if linea_programatica == RendicionCuentaMensual.LINEA_TRADICIONAL:
        datos["genera_acta_auditoria"] = False

    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
        datos=datos,
    )

    rendicion.refresh_from_db()
    assert not rendicion.acta_auditoria
    assert rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_FINALIZADA


@pytest.mark.django_db
def test_finalizar_sin_nuevo_archivo_conserva_acta_anterior():
    rendicion = _crear_rendicion(
        linea_programatica=RendicionCuentaMensual.LINEA_SECOS,
        acta_auditoria=SimpleUploadedFile(
            "acta-anterior.pdf",
            b"%PDF-1.4 acta anterior",
            content_type="application/pdf",
        ),
    )
    nombre_anterior = rendicion.acta_auditoria.name

    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
        datos={"monto_rendido": Decimal("100.00")},
    )

    rendicion.refresh_from_db()
    assert rendicion.acta_auditoria.name == nombre_anterior


@pytest.mark.django_db
def test_tradicional_con_no_finaliza_sin_rendiciones_incluidas():
    proyecto = _crear_proyecto("PROY-NO")
    rendicion = _crear_rendicion(proyecto=proyecto)
    form = RendicionProcesoForm(
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "150.00",
            "genera_acta_auditoria": "False",
        },
        rendicion=rendicion,
    )

    assert form.is_valid(), form.errors
    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
        datos=form.cleaned_data,
    )

    rendicion.refresh_from_db()
    assert rendicion.genera_acta_auditoria is False
    assert not rendicion.rendiciones_incluidas.exists()


@pytest.mark.django_db
def test_tradicional_con_si_admite_lista_vacia():
    rendicion = _crear_rendicion(proyecto=_crear_proyecto("PROY-ACTA-PROPIA"))
    form = RendicionProcesoForm(
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "100.00",
            "genera_acta_auditoria": "True",
        },
        rendicion=rendicion,
    )

    assert form.is_valid(), form.errors
    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
        datos=form.cleaned_data,
    )

    rendicion.refresh_from_db()
    assert rendicion.genera_acta_auditoria is True
    assert not rendicion.rendiciones_incluidas.exists()


@pytest.mark.django_db
def test_tradicional_con_si_persiste_seleccion_multiple_y_montos():
    proyecto = _crear_proyecto("PROY-SÍ")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=3)
    primera = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )
    segunda = _crear_rendicion(
        proyecto=proyecto,
        convenio="P02",
        numero_rendicion=2,
        genera_acta_auditoria=False,
    )
    form = RendicionProcesoForm(
        data={
            "accion_proceso": "finalizar_con_observaciones",
            "monto_rendido": "500.25",
            "monto_observado": "25.10",
            "genera_acta_auditoria": "True",
            "rendiciones_incluidas": [primera.pk, segunda.pk],
            "observaciones": "Se observaron comprobantes.",
        },
        rendicion=rendicion,
    )

    assert form.is_valid(), form.errors
    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_CON_OBSERVACIONES,
        datos=form.cleaned_data,
    )

    rendicion.refresh_from_db()
    assert rendicion.genera_acta_auditoria is True
    assert rendicion.monto_rendido == Decimal("500.25")
    assert rendicion.monto_observado == Decimal("25.10")
    assert set(rendicion.rendiciones_incluidas.all()) == {primera, segunda}


@pytest.mark.django_db
def test_tradicional_requiere_monto_rendido_y_respuesta_si_no():
    rendicion = _crear_rendicion(proyecto=_crear_proyecto("PROY-FALTANTES"))
    form = RendicionProcesoForm(
        data={"accion_proceso": "finalizar_sin_observaciones"},
        rendicion=rendicion,
    )

    assert not form.is_valid()
    assert form.errors["monto_rendido"] == ["Ingresá el monto rendido."]
    assert form.errors["genera_acta_auditoria"] == [
        "Indicá si se genera acta de auditoría."
    ]


@pytest.mark.django_db
def test_servicio_rechaza_rendiciones_si_se_indica_que_no_hay_acta():
    proyecto = _crear_proyecto("PROY-SIN-ACTA")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=2)
    candidata = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )

    with pytest.raises(ValidationError) as exc_info:
        RendicionProcesoService.ejecutar(
            rendicion=rendicion,
            accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
            datos={
                "monto_rendido": Decimal("100.00"),
                "genera_acta_auditoria": False,
                "rendiciones_incluidas": [candidata],
            },
        )

    assert "rendiciones_incluidas" in exc_info.value.message_dict


@pytest.mark.django_db
def test_formulario_rechaza_rendicion_de_otro_proyecto():
    rendicion = _crear_rendicion(proyecto=_crear_proyecto("PROY-FORM"))
    ajena = _crear_rendicion(
        proyecto=_crear_proyecto("PROY-FORM-AJENO"),
        genera_acta_auditoria=False,
    )
    form = RendicionProcesoForm(
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "100.00",
            "genera_acta_auditoria": "True",
            "rendiciones_incluidas": [ajena.pk],
        },
        rendicion=rendicion,
    )

    assert not form.is_valid()
    assert "rendiciones_incluidas" in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    "caso",
    ["otro_proyecto", "autorreferencia", "genera_acta", "sin_auditar"],
)
def test_servicio_rechaza_selecciones_no_elegibles_y_revierte(caso):
    proyecto = _crear_proyecto(f"PROY-{caso}")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=6)
    if caso == "otro_proyecto":
        candidata = _crear_rendicion(
            proyecto=_crear_proyecto("PROY-AJENO"),
            genera_acta_auditoria=False,
        )
    elif caso == "autorreferencia":
        candidata = rendicion
    elif caso == "genera_acta":
        candidata = _crear_rendicion(
            proyecto=proyecto,
            genera_acta_auditoria=True,
        )
    else:
        candidata = _crear_rendicion(
            proyecto=proyecto,
            genera_acta_auditoria=None,
        )

    with pytest.raises(ValidationError) as exc_info:
        RendicionProcesoService.ejecutar(
            rendicion=rendicion,
            accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
            datos={
                "monto_rendido": Decimal("900.00"),
                "monto_observado": Decimal("90.00"),
                "genera_acta_auditoria": True,
                "rendiciones_incluidas": [candidata],
                "acta_auditoria": SimpleUploadedFile(
                    "acta-no-persistida.pdf",
                    b"%PDF-1.4 no persistida",
                    content_type="application/pdf",
                ),
            },
        )

    assert "rendiciones_incluidas" in exc_info.value.message_dict
    rendicion.refresh_from_db()
    assert rendicion.monto_rendido is None
    assert rendicion.monto_observado is None
    assert rendicion.genera_acta_auditoria is None
    assert not rendicion.acta_auditoria
    assert rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_EN_CURSO
    assert not rendicion.rendiciones_incluidas.exists()


@pytest.mark.django_db
def test_cambio_posterior_de_elegibilidad_no_borra_asociacion_historica():
    proyecto = _crear_proyecto("PROY-HISTÓRICO")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=2)
    incluida = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )
    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
        datos={
            "monto_rendido": Decimal("100.00"),
            "genera_acta_auditoria": True,
            "rendiciones_incluidas": [incluida],
        },
    )

    incluida.genera_acta_auditoria = True
    incluida.save(update_fields=["genera_acta_auditoria"])

    assert list(rendicion.rendiciones_incluidas.all()) == [incluida]


@pytest.mark.django_db
def test_linea_secos_rechaza_rendiciones_incluidas():
    proyecto = _crear_proyecto("PROY-SECOS")
    rendicion = _crear_rendicion(
        proyecto=proyecto,
        linea_programatica=RendicionCuentaMensual.LINEA_SECOS,
    )
    candidata = _crear_rendicion(
        proyecto=proyecto,
        genera_acta_auditoria=False,
    )

    with pytest.raises(ValidationError) as exc_info:
        RendicionProcesoService.ejecutar(
            rendicion=rendicion,
            accion=RendicionProcesoService.ACCION_FINALIZAR_SIN_OBSERVACIONES,
            datos={
                "monto_rendido": Decimal("100.00"),
                "rendiciones_incluidas": [candidata],
            },
        )

    assert "rendiciones_incluidas" in exc_info.value.message_dict


@pytest.mark.django_db
def test_sin_permiso_de_auditoria_no_puede_finalizar(
    client,
    django_user_model,
):
    rendicion = _crear_rendicion(linea_programatica=RendicionCuentaMensual.LINEA_SECOS)
    usuario = django_user_model.objects.create_user(
        username="sin-permiso-auditoría",
        password="clave-segura",
    )
    client.force_login(usuario)

    response = client.post(
        reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk}),
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "100.00",
        },
    )

    assert response.status_code == 403
    rendicion.refresh_from_db()
    assert rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_EN_CURSO
    assert rendicion.monto_rendido is None


@pytest.mark.django_db
def test_selector_usa_la_etiqueta_de_proyecto_convenio_numero_y_periodo():
    proyecto = _crear_proyecto("PROY-ETIQUETA")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=2)
    incluida = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )

    field = RendicionProcesoForm(rendicion=rendicion).fields["rendiciones_incluidas"]

    assert field.label_from_instance(incluida) == (
        "Proyecto PROY-ETIQUETA - P01 - 1 - 01/09/2026 al 30/09/2026"
    )


@pytest.mark.django_db
def test_detalle_tradicional_muestra_campos_en_el_orden_requerido(
    client,
    superuser,
):
    rendicion = _crear_rendicion(proyecto=_crear_proyecto("PROY-VISTA"))
    client.force_login(superuser)

    response = client.get(
        reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
    )
    html = response.content.decode()

    assert response.status_code == 200
    posiciones = [
        html.index('name="monto_rendido"'),
        html.index('name="monto_observado"'),
        html.index('name="genera_acta_auditoria"'),
        html.index('name="rendiciones_incluidas"'),
        html.index('id="resultado-auditoria"'),
        html.index('name="observaciones"'),
    ]
    assert posiciones == sorted(posiciones)
    assert 'id="rendiciones-incluidas-container"' in html


@pytest.mark.django_db
def test_detalle_secos_mantiene_flujo_sin_campos_exclusivos_de_tradicional(
    client,
    superuser,
):
    rendicion = _crear_rendicion(linea_programatica=RendicionCuentaMensual.LINEA_SECOS)
    client.force_login(superuser)

    response = client.get(
        reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk})
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert 'name="monto_rendido"' in html
    assert 'name="acta_auditoria"' in html
    assert 'id="id_genera_acta_auditoria_' not in html
    assert 'id="id_rendiciones_incluidas"' not in html


@pytest.mark.django_db
def test_post_tradicional_entrega_la_rendicion_al_formulario(client, superuser):
    proyecto = _crear_proyecto("PROY-POST")
    rendicion = _crear_rendicion(proyecto=proyecto, numero_rendicion=2)
    incluida = _crear_rendicion(
        proyecto=proyecto,
        numero_rendicion=1,
        genera_acta_auditoria=False,
    )
    client.force_login(superuser)

    response = client.post(
        reverse("rendicioncuentasmensual_detail", kwargs={"pk": rendicion.pk}),
        data={
            "accion_proceso": "finalizar_sin_observaciones",
            "monto_rendido": "100.00",
            "genera_acta_auditoria": "True",
            "rendiciones_incluidas": [incluida.pk],
        },
    )

    assert response.status_code == 302
    rendicion.refresh_from_db()
    assert rendicion.genera_acta_auditoria is True
    assert list(rendicion.rendiciones_incluidas.all()) == [incluida]
    assert rendicion.subestado_proceso == RendicionCuentaMensual.SUBESTADO_FINALIZADA
