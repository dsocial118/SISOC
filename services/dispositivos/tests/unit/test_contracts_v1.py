import unittest

from services.dispositivos.application.contracts.v1 import (
    DispositivosActor,
    MunicipioCatalogo,
    ProvinciaCatalogo,
    SnapshotCatalogoTerritorial,
    TerritorialScope,
    get_geography_scope_map,
)


class IdentityContractV1Tests(unittest.TestCase):
    def test_actor_anonymous_does_not_broaden_the_geography_contract(self):
        actor = DispositivosActor.anonymous()

        self.assertFalse(actor.has_permission("dispositivos.view_dispositivo"))
        self.assertIsNone(get_geography_scope_map(actor))

    def test_province_scope_dominates_its_municipal_scopes(self):
        actor = DispositivosActor(
            actor_id=7,
            is_authenticated=True,
            is_superuser=False,
            is_territorial=True,
            scopes=(
                TerritorialScope(provincia_id=2, municipio_id=8),
                TerritorialScope(provincia_id=2),
            ),
        )

        self.assertEqual(get_geography_scope_map(actor), {2: None})


class CatalogContractV1Tests(unittest.TestCase):
    def test_snapshot_keeps_external_ids_and_version_as_data(self):
        snapshot = SnapshotCatalogoTerritorial(
            version="core-2026-08-28",
            provincias=(ProvinciaCatalogo(source_id=2, nombre="Buenos Aires"),),
            municipios=(
                MunicipioCatalogo(
                    source_id=8,
                    provincia_source_id=2,
                    nombre="La Plata",
                ),
            ),
        )

        self.assertEqual(snapshot.provincias[0].source_id, 2)
        self.assertEqual(snapshot.municipios[0].provincia_source_id, 2)
