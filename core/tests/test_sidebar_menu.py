import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


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

    assert 'style="order: 1;"' in content
    assert 'style="order: 2;"' in content
    assert 'style="order: 3;"' in content
    assert 'style="order: 4;"' in content
    assert 'style="order: 5;"' in content
    assert 'style="order: 6; border-bottom: 1px solid var(--lte-sidebar-color);"' in content
    assert "v06.04.26" in content
    assert 'class="footer-secondary-link"' in content
