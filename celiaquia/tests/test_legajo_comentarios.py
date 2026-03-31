from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    EstadoExpediente,
    EstadoLegajo,
    HistorialComentarios,
)
from core.models import Provincia
from users.models import Profile


@pytest.mark.django_db
def test_provincial_user_sees_comments_even_if_owner_without_province(client):
    provincia = Provincia.objects.create(nombre="La Rioja")

    owner = User.objects.create_user(username="owner", password="pw")
    owner_profile = Profile.objects.get(user=owner)
    owner_profile.provincia = None
    owner_profile.save()

    provincial = User.objects.create_user(username="prov_user", password="pw")
    profile = Profile.objects.get(user=provincial)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    perm_content_type = ContentType.objects.get_for_model(User)
    provincia_perm, _ = Permission.objects.get_or_create(
        codename="role_provinciaceliaquia",
        defaults={
            "name": "Permiso provincia Celiaquia",
            "content_type": perm_content_type,
        },
    )
    provincial.user_permissions.add(provincia_perm)

    expediente_ct = ContentType.objects.get_for_model(Expediente)
    view_perm, _ = Permission.objects.get_or_create(
        codename="view_expediente",
        content_type=expediente_ct,
        defaults={"name": "Can view expediente"},
    )
    provincial.user_permissions.add(view_perm)

    estado_exp = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    ciudadano = Ciudadano.objects.create(
        apellido="Pérez",
        nombre="Ana",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
    )

    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado_exp)
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    comentario_usuario = User.objects.create_user(username="tecnico", password="pw")
    comentario = HistorialComentarios.objects.create(
        legajo=legajo,
        tipo_comentario=HistorialComentarios.TIPO_OBSERVACION_GENERAL,
        comentario="Revisión técnica",
        usuario=comentario_usuario,
    )

    client.force_login(provincial)
    response = client.get(
        reverse(
            "legajo_comentarios_list",
            kwargs={"expediente_id": expediente.pk, "legajo_id": legajo.pk},
        )
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"]
    assert any(item["id"] == comentario.pk for item in payload["comentarios"])
