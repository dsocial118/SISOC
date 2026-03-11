import pytest
from django.db import IntegrityError, transaction

from admisiones.models.admisiones import Admision
from comedores.models import Comedor, Nomina
from core.models import Dia, Provincia
from pwa.models import (
    ActividadEspacioPWA,
    CatalogoActividadPWA,
    InscriptoActividadEspacioPWA,
)


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Actividades", provincia=provincia)


@pytest.fixture
def dia_actividad(db):
    return Dia.objects.create(nombre="Lunes")


@pytest.fixture
def admision(comedor):
    return Admision.objects.create(comedor=comedor, activa=True)


@pytest.mark.django_db
def test_catalogo_actividades_seed_inicial_existe():
    assert CatalogoActividadPWA.objects.filter(
        categoria="Cultura",
        actividad="Taller de pintura",
        activo=True,
    ).exists()


@pytest.mark.django_db
def test_catalogo_actividad_no_permite_duplicado_categoria_actividad():
    CatalogoActividadPWA.objects.create(
        categoria="Cultura", actividad="Jazz de prueba único", activo=True
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CatalogoActividadPWA.objects.create(
                categoria="Cultura",
                actividad="Jazz de prueba único",
                activo=True,
            )


@pytest.mark.django_db
def test_inscripto_actividad_permite_reingreso_tras_baja_logica(
    comedor, admision, dia_actividad
):
    catalogo = CatalogoActividadPWA.objects.create(
        categoria="Deporte",
        actividad="Basquet de prueba",
        activo=True,
    )
    actividad = ActividadEspacioPWA.objects.create(
        comedor=comedor,
        catalogo_actividad=catalogo,
        dia_actividad=dia_actividad,
        horario_actividad="18:00 a 19:30",
        activo=True,
    )
    nomina = Nomina.objects.create(admision=admision, estado=Nomina.ESTADO_ACTIVO)

    inscripto = InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
    )
    inscripto.activo = False
    inscripto.save(update_fields=["activo"])

    nuevo = InscriptoActividadEspacioPWA.objects.create(
        actividad_espacio=actividad,
        nomina=nomina,
        activo=True,
    )

    assert nuevo.id != inscripto.id
