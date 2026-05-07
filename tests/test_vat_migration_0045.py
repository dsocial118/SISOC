import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group, User

from VAT.models import Centro
from core.models import Localidad, Municipio, Provincia


pytestmark = pytest.mark.django_db

migration_module = importlib.import_module(
    "VAT.migrations.0045_centro_referentes_revisores"
)


def test_migration_copia_referente_legacy_a_referentes_m2m():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    group, _ = Group.objects.get_or_create(name="CFP")
    referente = User.objects.create_user(username="referente-migracion")
    referente.groups.add(group)
    centro = Centro.objects.create(
        nombre="Centro migracion",
        codigo="MIG-001",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="7",
        numero=123,
        domicilio_actividad="Calle 7 123",
        telefono="221-111111",
        celular="221-222222",
        correo="migracion@vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221-333333",
        correo_referente="ana@vat.test",
        referente=referente,
        tipo_gestion="Estatal",
        clase_institucion="Formacion Profesional",
        situacion="Institucion de ETP",
        activo=True,
    )

    migration_module.copy_legacy_referente_to_referentes(apps, None)

    assert list(centro.referentes.values_list("pk", flat=True)) == [referente.pk]
