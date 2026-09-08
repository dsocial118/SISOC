"""Paridad del backoffice con lo que carga la app (fase 3).

Cubre: detalle por instancia (con N instancias por ciclo), edición completa
de una instancia, revisión del coordinador sobre seguimientos y el ABM de
actas complementarias extraordinarias.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import (
    ActaComplementaria,
    FuncionamientoSeguimiento,
    PrestacionSeguimiento,
    PrimerSeguimiento,
    Relevamiento,
)

MANAGEMENT_VACIO = {
    "prestaciones-TOTAL_FORMS": "1",
    "prestaciones-INITIAL_FORMS": "0",
    "prestaciones-MIN_NUM_FORMS": "0",
    "prestaciones-MAX_NUM_FORMS": "1000",
}


@pytest.fixture
def comedor():
    provincia = Provincia.objects.create(nombre="Prov Backoffice F3")
    return Comedor.objects.create(nombre="Comedor Backoffice F3", provincia=provincia)


@pytest.fixture
def relevamiento(comedor):
    return Relevamiento.objects.create(comedor=comedor, estado="En Proceso")


@pytest.fixture
def ciclo(relevamiento):
    primer = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        tipo=PrimerSeguimiento.TIPO_PRIMER,
        numero_orden=1,
        estado=PrimerSeguimiento.ESTADO_COMPLETO,
    )
    posterior = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
        numero_orden=2,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        origen=PrimerSeguimiento.ORIGEN_APP,
    )
    return primer, posterior


def _login(client, *codenames, username="bo_f3"):
    user = get_user_model().objects.create_user(username=username, password="x")
    if codenames:
        user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
    client.force_login(user)
    return user


def _kw(seguimiento):
    return {
        "comedor_pk": seguimiento.id_relevamiento.comedor_id,
        "relevamiento_pk": seguimiento.id_relevamiento_id,
        "pk": seguimiento.pk,
    }


# --------------------------------------------------------------------------- #
# Detalle por instancia
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_detalle_por_pk_muestra_la_instancia_pedida(client, ciclo):
    _, posterior = ciclo
    _login(client, "view_relevamiento")

    response = client.get(reverse("seguimiento_detalle", kwargs=_kw(posterior)))

    assert response.status_code == 200
    contenido = response.content.decode()
    assert "Seguimiento posterior #2" in contenido
    # Badge de origen: esta instancia la cargo el territorial desde la app.
    assert "desde la app" in contenido
    # Navegacion entre las instancias del ciclo.
    assert "#1 Primer seguimiento" in contenido


@pytest.mark.django_db
def test_ruta_historica_con_varias_instancias_no_rompe(client, ciclo, relevamiento):
    """Antes resolvia con get() por relevamiento: con 2 instancias daba 500."""
    _login(client, "view_relevamiento")

    response = client.get(
        reverse(
            "primer_seguimiento_detalle",
            kwargs={
                "comedor_pk": relevamiento.comedor_id,
                "relevamiento_pk": relevamiento.id,
            },
        )
    )

    assert response.status_code == 200
    assert "Primer seguimiento #1" in response.content.decode()


@pytest.mark.django_db
def test_detalle_relevamiento_lista_todas_las_instancias(client, ciclo, relevamiento):
    primer, posterior = ciclo
    _login(client, "view_relevamiento")

    response = client.get(
        reverse(
            "relevamiento_detalle",
            kwargs={"comedor_pk": relevamiento.comedor_id, "pk": relevamiento.id},
        )
    )

    assert response.status_code == 200
    contenido = response.content.decode()
    assert reverse("seguimiento_detalle", kwargs=_kw(primer)) in contenido
    assert reverse("seguimiento_detalle", kwargs=_kw(posterior)) in contenido
    assert "2 instancias" in contenido


@pytest.mark.django_db
def test_eliminar_por_pk_borra_solo_esa_instancia(client, ciclo, mocker):
    primer, posterior = ciclo
    _login(client, "delete_primerseguimiento")
    mocker.patch("relevamientos.signals.AsyncRemovePrimerSeguimientoToGestionar.start")

    response = client.post(reverse("seguimiento_eliminar", kwargs=_kw(posterior)))

    assert response.status_code == 302
    assert not PrimerSeguimiento.objects.filter(pk=posterior.pk).exists()
    assert PrimerSeguimiento.objects.filter(pk=primer.pk).exists()


# --------------------------------------------------------------------------- #
# Edicion completa
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_editar_seguimiento_requiere_permiso(client, ciclo):
    primer, _ = ciclo
    _login(client, "view_relevamiento")

    response = client.get(reverse("seguimiento_editar", kwargs=_kw(primer)))

    assert response.status_code == 403


@pytest.mark.django_db
def test_editar_seguimiento_renderiza_todos_los_bloques(client, ciclo):
    primer, _ = ciclo
    _login(client, "change_primerseguimiento")

    response = client.get(reverse("seguimiento_editar", kwargs=_kw(primer)))

    assert response.status_code == 200
    contenido = response.content.decode()
    for key in ("funcionamiento", "menu", "cierre", "acta_excepcion", "prestaciones"):
        assert f'id="bloque-{key}"' in contenido
    assert 'name="seg-estado"' in contenido


@pytest.mark.django_db
def test_editar_seguimiento_guarda_raiz_bloque_nuevo_y_prestacion(client, ciclo):
    primer, _ = ciclo
    _login(client, "change_primerseguimiento")
    assert primer.funcionamiento is None

    datos = {
        "seg-estado": PrimerSeguimiento.ESTADO_EN_PROCESO,
        "seg-tecnico": "Tecnica Norte",
        "seg-fecha_hora": "2026-09-05T10:30",
        "funcionamiento-funcionamiento": FuncionamientoSeguimiento.ABIERTO_FUNCIONANDO,
        "prestaciones-0-dias_prestacion": "Lunes",
        "prestaciones-0-tipo_prestacion": "Almuerzo",
        "prestaciones-0-ap_presencial": "25",
        **MANAGEMENT_VACIO,
    }
    response = client.post(reverse("seguimiento_editar", kwargs=_kw(primer)), datos)

    assert response.status_code == 302
    assert response.url == reverse("seguimiento_detalle", kwargs=_kw(primer))
    primer.refresh_from_db()
    assert primer.estado == PrimerSeguimiento.ESTADO_EN_PROCESO
    assert primer.tecnico == "Tecnica Norte"
    assert primer.fecha_hora is not None
    # Solo se creo el bloque que tenia datos; el resto sigue sin cargar.
    assert primer.funcionamiento is not None
    assert (
        primer.funcionamiento.funcionamiento
        == FuncionamientoSeguimiento.ABIERTO_FUNCIONANDO
    )
    assert primer.cierre is None
    assert primer.menu is None
    prestacion = PrestacionSeguimiento.objects.get(seguimiento=primer)
    assert (prestacion.dias_prestacion, prestacion.ap_presencial) == ("Lunes", 25)
    # Lo editado desde el backoffice sigue siendo origen SISOC.
    assert primer.origen == PrimerSeguimiento.ORIGEN_SISOC


@pytest.mark.django_db
def test_editar_seguimiento_con_error_no_guarda_y_muestra_el_error(client, ciclo):
    primer, _ = ciclo
    _login(client, "change_primerseguimiento")

    datos = {
        "seg-estado": "Estado inventado",
        **MANAGEMENT_VACIO,
    }
    response = client.post(reverse("seguimiento_editar", kwargs=_kw(primer)), datos)

    assert response.status_code == 200
    assert "Revise los campos marcados" in response.content.decode()
    primer.refresh_from_db()
    assert primer.estado == PrimerSeguimiento.ESTADO_COMPLETO


# --------------------------------------------------------------------------- #
# Revision del coordinador sobre la instancia
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_revisar_seguimiento_a_subsanar_exige_observaciones(client, ciclo):
    primer, _ = ciclo
    _login(client, "review_relevamiento")

    response = client.post(
        reverse("seguimiento_revision_coordinador", kwargs=_kw(primer)),
        {"estado_validacion": PrimerSeguimiento.ESTADO_VALIDACION_A_SUBSANAR},
    )

    assert response.status_code == 302
    primer.refresh_from_db()
    assert primer.estado_validacion is None


@pytest.mark.django_db
def test_revisar_seguimiento_guarda_resultado_y_coordinador(client, ciclo):
    primer, _ = ciclo
    coordinador = _login(client, "review_relevamiento")

    response = client.post(
        reverse("seguimiento_revision_coordinador", kwargs=_kw(primer)),
        {
            "estado_validacion": PrimerSeguimiento.ESTADO_VALIDACION_A_SUBSANAR,
            "observaciones_coordinador": "Falta la foto del menú.",
        },
    )

    assert response.status_code == 302
    primer.refresh_from_db()
    assert primer.estado_validacion == PrimerSeguimiento.ESTADO_VALIDACION_A_SUBSANAR
    assert primer.observaciones_coordinador == "Falta la foto del menú."
    assert primer.coordinador == coordinador
    assert primer.fecha_revision_coordinador is not None


@pytest.mark.django_db
def test_revisar_seguimiento_sin_permiso_403(client, ciclo):
    primer, _ = ciclo
    _login(client, "view_relevamiento")

    response = client.post(
        reverse("seguimiento_revision_coordinador", kwargs=_kw(primer)),
        {"estado_validacion": PrimerSeguimiento.ESTADO_VALIDACION_VALIDADO},
    )

    assert response.status_code == 403


# --------------------------------------------------------------------------- #
# Actas complementarias extraordinarias
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_crear_acta_con_prestaciones_queda_origen_sisoc(client, comedor):
    usuario = _login(client, "add_actacomplementaria")

    datos = {
        "acta-fecha_hora": "2026-09-05T09:00",
        "acta-observaciones": "Se suma la cena los viernes.",
        "prestaciones-0-dias_prestacion": "Viernes",
        "prestaciones-0-tipo_prestacion": "Cena",
        "prestaciones-0-cantidad_actual": "40",
        "prestaciones-0-cantidad_espera": "5",
        **MANAGEMENT_VACIO,
    }
    response = client.post(
        reverse("acta_complementaria_crear", kwargs={"comedor_pk": comedor.pk}), datos
    )

    acta = ActaComplementaria.objects.get(comedor=comedor)
    assert response.status_code == 302
    assert response.url == reverse(
        "acta_complementaria_detalle", kwargs={"comedor_pk": comedor.pk, "pk": acta.pk}
    )
    assert acta.origen == ActaComplementaria.ORIGEN_SISOC
    # Sin tecnico elegido queda quien cargo el acta.
    assert acta.tecnico == usuario
    prestacion = acta.prestaciones.get()
    assert (prestacion.tipo_prestacion, prestacion.cantidad_actual) == ("Cena", 40)


@pytest.mark.django_db
def test_editar_acta_agrega_prestacion_y_conserva_las_existentes(client, comedor):
    _login(client, "change_actacomplementaria")
    acta = ActaComplementaria.objects.create(comedor=comedor, observaciones="Inicial")
    existente = acta.prestaciones.create(
        dias_prestacion="Lunes", tipo_prestacion="Almuerzo", cantidad_actual=10
    )

    datos = {
        "acta-observaciones": "Editada",
        "prestaciones-TOTAL_FORMS": "2",
        "prestaciones-INITIAL_FORMS": "1",
        "prestaciones-MIN_NUM_FORMS": "0",
        "prestaciones-MAX_NUM_FORMS": "1000",
        "prestaciones-0-id": str(existente.pk),
        "prestaciones-0-acta": str(acta.pk),
        "prestaciones-0-dias_prestacion": "Lunes",
        "prestaciones-0-tipo_prestacion": "Almuerzo",
        "prestaciones-0-cantidad_actual": "12",
        "prestaciones-1-dias_prestacion": "Martes",
        "prestaciones-1-tipo_prestacion": "Merienda",
        "prestaciones-1-cantidad_actual": "8",
    }
    response = client.post(
        reverse(
            "acta_complementaria_editar",
            kwargs={"comedor_pk": comedor.pk, "pk": acta.pk},
        ),
        datos,
    )

    assert response.status_code == 302
    acta.refresh_from_db()
    assert acta.observaciones == "Editada"
    filas = sorted(acta.prestaciones.values_list("dias_prestacion", "cantidad_actual"))
    assert filas == [("Lunes", 12), ("Martes", 8)]


@pytest.mark.django_db
def test_detalle_y_eliminar_acta(client, comedor):
    _login(client, "view_relevamiento", "delete_actacomplementaria")
    acta = ActaComplementaria.objects.create(
        comedor=comedor,
        observaciones="Para borrar",
        origen=ActaComplementaria.ORIGEN_APP,
    )

    detalle = client.get(
        reverse(
            "acta_complementaria_detalle",
            kwargs={"comedor_pk": comedor.pk, "pk": acta.pk},
        )
    )
    assert detalle.status_code == 200
    assert "Para borrar" in detalle.content.decode()
    assert "desde la app" in detalle.content.decode()

    borrado = client.post(
        reverse(
            "acta_complementaria_eliminar",
            kwargs={"comedor_pk": comedor.pk, "pk": acta.pk},
        )
    )
    assert borrado.status_code == 302
    assert not ActaComplementaria.objects.filter(pk=acta.pk).exists()


@pytest.mark.django_db
def test_acta_de_otro_comedor_da_404(client, comedor):
    _login(client, "change_actacomplementaria")
    otro = Comedor.objects.create(nombre="Otro comedor F3")
    acta = ActaComplementaria.objects.create(comedor=otro)

    response = client.get(
        reverse(
            "acta_complementaria_editar",
            kwargs={"comedor_pk": comedor.pk, "pk": acta.pk},
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_listado_de_relevamientos_muestra_actas_e_instancias(client, comedor, ciclo):
    _login(client, "view_relevamiento", "add_actacomplementaria")
    acta = ActaComplementaria.objects.create(
        comedor=comedor, origen=ActaComplementaria.ORIGEN_APP
    )
    acta.prestaciones.create(dias_prestacion="Lunes", tipo_prestacion="Almuerzo")

    response = client.get(reverse("relevamientos", kwargs={"comedor_pk": comedor.pk}))

    assert response.status_code == 200
    contenido = response.content.decode()
    assert "Actas complementarias extraordinarias" in contenido
    assert (
        reverse(
            "acta_complementaria_detalle",
            kwargs={"comedor_pk": comedor.pk, "pk": acta.pk},
        )
        in contenido
    )
    assert "1 prestación" in contenido
    assert (
        reverse("acta_complementaria_crear", kwargs={"comedor_pk": comedor.pk})
        in contenido
    )
    # Cada instancia del ciclo linkea a su propio detalle.
    for seguimiento in ciclo:
        assert reverse("seguimiento_detalle", kwargs=_kw(seguimiento)) in contenido
    assert "Seguimiento posterior #2" in contenido
