import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from core.constants import UserGroups


pytestmark = pytest.mark.django_db


def test_sidebar_separa_administracion_de_configuracion_comedores(client):
    user_model = get_user_model()
    user = user_model.objects.create_superuser(
        username="sidebar_admin",
        email="sidebar_admin@example.com",
        password="testpass123",
    )
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    admin_start = content.index("Administración del sistema")
    config_start = content.index("Configuración de Comedores")
    legajos_start = content.index("Legajos")
    admin_block = content[admin_start:config_start]
    config_block = content[config_start:legajos_start]

    assert reverse("usuarios") in admin_block
    assert reverse("grupos") in admin_block
    assert reverse("programa_listar") in admin_block
    assert reverse("audittrail:log_list") in admin_block
    assert reverse("papelera_list") in admin_block
    assert reverse("dupla_list") not in admin_block
    assert reverse("montoprestacion_listar") not in admin_block
    assert "Parametrías de Voucher" in admin_block
    assert "Programas" in admin_block

    assert reverse("dupla_list") in config_block
    assert reverse("montoprestacion_listar") in config_block
    assert reverse("usuarios") not in config_block
    assert reverse("grupos") not in config_block

    for expected_order in range(1, 7):
        assert f"order: {expected_order}" in content

    assert reverse("changelog") in content
    assert 'class="footer-secondary-link"' in content
    assert re.search(r">v\d{2}\.\d{2}\.\d{2}<", content)


def test_sidebar_oculta_modalidades_para_cfpinet(client):
    user_model = get_user_model()
    user = user_model.objects.create_superuser(
        username="sidebar_cfpinet",
        email="sidebar_cfpinet@example.com",
        password="testpass123",
    )
    cfpinet_group, _ = Group.objects.get_or_create(name="CFPINET")
    user.groups.add(cfpinet_group)
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    assert "Planes Curriculares" in content
    assert "Modalidades de Cursado" not in content


def test_sidebar_mantiene_expedientes_de_pago_visible_para_importador(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="sidebar_importador",
        password="testpass123",
    )
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="importarexpediente",
            codename="view_archivosimportados",
        )
    )
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    assert "Comedores" in content
    assert reverse("importarexpedientes_list") in content
    assert "Expedientes de Pago" in content
    assert "Ver Importar Expediente de Pago" not in content


def test_sidebar_ubica_expedientes_de_pago_cuarto_en_comedores(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="sidebar_comedores_importador",
        password="testpass123",
    )
    for app_label, codename in (
        ("comedores", "view_comedor"),
        ("admisiones", "view_admision"),
        ("acompanamientos", "view_informacionrelevante"),
        ("importarexpediente", "view_archivosimportados"),
    ):
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
        )
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    comedores_start = content.index("<p>Comedores</p>")
    organizaciones_start = content.index("<!-- ORGANIZACIONES -->")
    comedores_block = content[comedores_start:organizaciones_start]

    assert comedores_block.index("Ver Comedores") < comedores_block.index(
        "Admisión - Comedores"
    )
    assert comedores_block.index("Admisión - Comedores") < comedores_block.index(
        "Acompañamiento"
    )
    assert comedores_block.index("Acompañamiento") < comedores_block.index(
        "Expedientes de Pago"
    )


def test_sidebar_muestra_ocr_a_usuario_con_solo_permiso_ocr(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="sidebar_ocr",
        password="testpass123",
    )
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label="ocr", codename="use_ocr")
    )
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    assert reverse("ocr_upload") in content
    assert "<p>OCR</p>" in content
    assert "Administración del sistema" not in content


def test_sidebar_ubica_ocr_entre_configuracion_y_comunicados(client):
    user_model = get_user_model()
    user = user_model.objects.create_superuser(
        username="sidebar_ocr_admin",
        password="testpass123",
    )
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200

    content = response.content.decode()
    admin_start = content.index("Administración del sistema")
    config_start = content.index("Configuración de Comedores")
    admin_block = content[admin_start:config_start]

    assert reverse("ocr_upload") not in admin_block
    assert re.search(
        r'style="order: 5">.*?<p>Configuración de Comedores</p>', content, re.S
    )
    assert re.search(r'style="order: 6">.*?<p>OCR</p>', content, re.S)
    assert re.search(r'style="order: 7;.*?<p>Comunicados</p>', content, re.S)


def test_sidebar_oculta_comunicados_a_usuario_solo_cdi_local(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="sidebar-cdi-local",
        password="testpass123",
    )
    grupo, _ = Group.objects.get_or_create(name=UserGroups.CDI_REFERENTE_CENTRO)
    user.groups.add(grupo)
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200
    assert "<p>Comunicados</p>" not in response.content.decode()
    assert client.get(reverse("comunicados")).status_code == 200


def test_sidebar_muestra_comunicados_a_usuario_cdi_con_rol_simepi(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="sidebar-cdi-simepi",
        password="testpass123",
    )
    for nombre in (
        UserGroups.CDI_REFERENTE_CENTRO,
        UserGroups.SIMEPI_EGP,
    ):
        grupo, _ = Group.objects.get_or_create(name=nombre)
        user.groups.add(grupo)
    client.force_login(user)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200
    assert "<p>Comunicados</p>" in response.content.decode()
