import pytest

from dispositivos.models import (
    EstadoProyeccionTerritorial,
    MunicipioTerritorialProyectado,
    ProvinciaTerritorialProyectada,
    VersionProyeccionTerritorial,
)
from dispositivos.territorial_projection import (
    MunicipioTerritorial,
    ProvinciaTerritorial,
    aplicar_proyeccion_territorial,
)


@pytest.mark.django_db
def test_aplicar_proyeccion_publica_snapshot_completo_y_activa_una_version():
    anterior = aplicar_proyeccion_territorial(
        version="catalogo-v1",
        provincias=[ProvinciaTerritorial(source_id=1, nombre="Buenos Aires")],
        municipios=[
            MunicipioTerritorial(
                source_id=10,
                provincia_source_id=1,
                nombre="La Plata",
            )
        ],
    )

    actual = aplicar_proyeccion_territorial(
        version="catalogo-v2",
        provincias=[ProvinciaTerritorial(source_id=2, nombre="Santa Fe")],
        municipios=[
            MunicipioTerritorial(
                source_id=20,
                provincia_source_id=2,
                nombre="Rosario",
            )
        ],
    )

    assert EstadoProyeccionTerritorial.objects.get(singleton=1).version == actual
    assert VersionProyeccionTerritorial.objects.count() == 2
    assert (
        ProvinciaTerritorialProyectada.objects.filter(version=actual).get().source_id
        == 2
    )
    municipio = MunicipioTerritorialProyectado.objects.filter(version=actual).get()
    assert municipio.source_id == 20
    assert municipio.provincia.source_id == 2


@pytest.mark.django_db
def test_aplicar_proyeccion_es_idempotente_para_una_version_existente():
    original = aplicar_proyeccion_territorial(
        version="catalogo-v1",
        provincias=[ProvinciaTerritorial(source_id=1, nombre="Buenos Aires")],
        municipios=[],
    )

    repeated = aplicar_proyeccion_territorial(
        version="catalogo-v1",
        provincias=[ProvinciaTerritorial(source_id=2, nombre="Santa Fe")],
        municipios=[],
    )

    assert repeated.pk == original.pk
    assert ProvinciaTerritorialProyectada.objects.filter(version=original).count() == 1


@pytest.mark.django_db
def test_aplicar_proyeccion_rechaza_municipio_sin_provincia_en_el_snapshot():
    with pytest.raises(ValueError, match="provincia inexistente"):
        aplicar_proyeccion_territorial(
            version="catalogo-invalido",
            provincias=[],
            municipios=[
                MunicipioTerritorial(
                    source_id=10,
                    provincia_source_id=1,
                    nombre="La Plata",
                )
            ],
        )
