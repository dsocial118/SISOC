from datetime import date

import pytest
from django.contrib.auth.models import User

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.models import ProfileTerritorialScope
from users.territorial_scope import apply_territorial_scope


def _crear_ciudadano(documento, provincia, municipio, localidad):
    return Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )


@pytest.mark.django_db
def test_scope_municipio_no_incluye_otro_municipio():
    provincia = Provincia.objects.create(nombre="Scope Municipio Provincia")
    municipio_a = Municipio.objects.create(
        nombre="Scope Municipio A", provincia=provincia
    )
    localidad_a = Localidad.objects.create(
        nombre="Scope Localidad A", municipio=municipio_a
    )
    municipio_b = Municipio.objects.create(
        nombre="Scope Municipio B", provincia=provincia
    )
    localidad_b = Localidad.objects.create(
        nombre="Scope Localidad B", municipio=municipio_b
    )
    user = User.objects.create_user(username="scope_municipio", password="pass")
    user.profile.es_usuario_provincial = True
    user.profile.save()
    ProfileTerritorialScope.objects.create(
        profile=user.profile,
        provincia=provincia,
        municipio=municipio_a,
    )
    visible = _crear_ciudadano(101, provincia, municipio_a, localidad_a)
    oculto = _crear_ciudadano(102, provincia, municipio_b, localidad_b)

    queryset = apply_territorial_scope(
        Ciudadano.objects.all(),
        user,
        provincia_lookup="provincia_id",
        municipio_lookup="municipio_id",
        localidad_lookup="localidad_id",
    )

    assert visible in queryset
    assert oculto not in queryset


@pytest.mark.django_db
def test_scope_localidad_no_incluye_otra_localidad():
    provincia = Provincia.objects.create(nombre="Scope Localidad Provincia")
    municipio = Municipio.objects.create(
        nombre="Scope Localidad Municipio", provincia=provincia
    )
    localidad_a = Localidad.objects.create(
        nombre="Scope Localidad A", municipio=municipio
    )
    localidad_b = Localidad.objects.create(
        nombre="Scope Localidad B", municipio=municipio
    )
    user = User.objects.create_user(username="scope_localidad", password="pass")
    user.profile.es_usuario_provincial = True
    user.profile.save()
    ProfileTerritorialScope.objects.create(
        profile=user.profile,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_a,
    )
    visible = _crear_ciudadano(201, provincia, municipio, localidad_a)
    oculto = _crear_ciudadano(202, provincia, municipio, localidad_b)

    queryset = apply_territorial_scope(
        Ciudadano.objects.all(),
        user,
        provincia_lookup="provincia_id",
        municipio_lookup="municipio_id",
        localidad_lookup="localidad_id",
    )

    assert visible in queryset
    assert oculto not in queryset
