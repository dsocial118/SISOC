"""Contrato del template compartido `vat/oferta_institucional/comision_detail.html`.

Lo renderizan dos views sobre modelos distintos: `ComisionCursoDetailView`
(camino Curso -> ComisionCurso, el activo) y `ComisionDetailView` (camino legacy
OfertaInstitucional -> Comision). Las features que existen solo en el camino
Curso deben quedar fuera del render legacy, que no tiene sus endpoints.

Se usa `RequestFactory` en lugar del test client a proposito: el venv local corre
Python 3.14 con Django 4.2 y la instrumentacion de templates del test client
falla ahi (ver docs/registro/cambios/2026-07-27-vat-comision-resultados-acta.md).
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.test import RequestFactory
from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Programa, Provincia, Sexo
from VAT.models import (
    Centro,
    Comision,
    ComisionCurso,
    Curso,
    Inscripcion,
    InstitucionUbicacion,
    ModalidadCursada,
    OfertaInstitucional,
    PlanVersionCurricular,
    Sector,
)
from VAT.views.curso import ComisionCursoDetailView
from VAT.views.oferta_institucional import ComisionDetailView


def _render(view, pk, user):
    request = RequestFactory().get("/x/")
    request.user = user
    request.csp_nonce = "n"
    return view.as_view()(request, pk=pk).render().content.decode()


@pytest.fixture
def escenario(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="LP rev", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa rev", municipio=municipio)
    modalidad = ModalidadCursada.objects.create(nombre="Pres rev", activo=True)
    sector = Sector.objects.create(nombre="Sector rev")
    programa = Programa.objects.create(nombre="Prog rev")
    sexo = Sexo.objects.create(sexo="NB rev")
    Group.objects.get_or_create(name="CFP")
    user = User.objects.create_superuser(
        username="rev-admin", email="r@r.test", password="x"
    )
    centro = Centro.objects.create(
        nombre="CFP rev",
        codigo="060188001",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="1",
        numero=1,
        domicilio_actividad="C 1",
        telefono="1",
        celular="1",
        correo="a@a.test",
        nombre_referente="A",
        apellido_referente="B",
        telefono_referente="1",
        correo_referente="b@b.test",
        referente=user,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=True,
    )
    ubicacion = InstitucionUbicacion.objects.create(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        domicilio="C 1",
        es_principal=True,
    )
    curso = Curso.objects.create(
        centro=centro, nombre="Curso rev", modalidad=modalidad, estado="activo"
    )
    comision_curso = ComisionCurso.objects.create(
        curso=curso,
        ubicacion=ubicacion,
        codigo_comision="REV-CC",
        nombre="CC rev",
        cupo_total=10,
        fecha_inicio=timezone.localdate() - timedelta(days=10),
        fecha_fin=timezone.localdate() + timedelta(days=10),
        estado="activa",
    )
    plan = PlanVersionCurricular.objects.create(
        nombre="Plan rev",
        provincia=provincia,
        sector=sector,
        modalidad_cursada=modalidad,
        activo=True,
    )
    oferta = OfertaInstitucional.objects.create(
        centro=centro,
        plan_curricular=plan,
        programa=programa,
        nombre_local="Oferta rev",
        ciclo_lectivo=2026,
        estado="publicada",
    )
    comision_legacy = Comision.objects.create(
        oferta=oferta,
        ubicacion=ubicacion,
        codigo_comision="REV-LEG",
        nombre="Legacy rev",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 7, 1),
        cupo=20,
        estado="activa",
    )
    for i, target in enumerate((comision_curso, comision_legacy)):
        ciudadano = Ciudadano.objects.create(
            apellido=f"Rev{i}",
            nombre="Alumno",
            fecha_nacimiento=date(2000, 1, 1),
            tipo_documento=Ciudadano.DOCUMENTO_DNI,
            documento=44000000 + i,
            sexo=sexo,
        )
        kwargs = (
            {"comision_curso": target}
            if isinstance(target, ComisionCurso)
            else {"comision": target}
        )
        Inscripcion.objects.create(
            ciudadano=ciudadano,
            programa=programa,
            estado="inscripta",
            origen_canal="backoffice",
            **kwargs,
        )
    return user, comision_curso, comision_legacy


@pytest.mark.django_db
def test_camino_curso_tiene_lote_y_resultados(escenario):
    user, cc, _ = escenario
    html = _render(ComisionCursoDetailView, cc.pk, user)

    assert 'id="formInscriptosLote"' in html
    assert "cambiar-estado-lote" in html
    assert 'class="ci-lote-check"' in html
    assert 'data-sisoc-tab-target="resultados"' in html
    assert "<th>Tipo de alumno</th>" in html
    panel = html.split('data-sisoc-panel="inscriptos"')[1].split(
        'data-sisoc-panel="sesiones"'
    )[0]
    assert 'colspan="10"' in panel


@pytest.mark.django_db
def test_camino_legacy_no_renderiza_lote_ni_resultados(escenario):
    user, _, legacy = escenario
    html = _render(ComisionDetailView, legacy.pk, user)

    # Nada de la UI de lote: no hay endpoint de lote para este camino.
    assert 'id="formInscriptosLote"' not in html
    assert 'class="ci-lote-check"' not in html
    assert 'id="inscriptosLoteAceptar"' not in html
    assert 'id="modalInscriptosLote"' not in html
    assert "cambiar-estado-lote" not in html
    assert 'name="estado" id="inscriptosLoteEstado"' not in html
    # La solapa Resultados tampoco (es solo del camino ComisionCurso).
    assert 'data-sisoc-tab-target="resultados"' not in html
    # Las columnas Estado y Tipo de alumno si se agregan en ambos caminos.
    assert "<th>Estado</th>" in html
    assert "<th>Tipo de alumno</th>" in html
    # colspan correcto DENTRO del panel de inscriptos: 8 base + acciones, sin
    # checkbox. Se acota al panel porque la tabla de Clases usa 9 legitimamente.
    panel = html.split('data-sisoc-panel="inscriptos"')[1].split(
        'data-sisoc-panel="sesiones"'
    )[0]
    assert 'colspan="9"' in panel
    assert 'colspan="10"' not in panel
