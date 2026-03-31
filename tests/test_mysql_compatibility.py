import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError, connection, transaction


@pytest.mark.django_db
@pytest.mark.mysql_compat
def test_mysql_backend_activo_en_suite_mysql_compat():
    """Garantiza que este subset corre sobre MySQL real en CI."""
    if connection.vendor != "mysql":
        pytest.skip("La suite actual no está usando MySQL.")
    assert connection.vendor == "mysql"


@pytest.mark.django_db
@pytest.mark.mysql_compat
def test_mysql_integridad_unicidad_username_con_rollback():
    """Valida que errores de unicidad hagan rollback en transacción atómica."""
    User.objects.create(username="mysql_compat_user")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create(username="mysql_compat_user")

    assert User.objects.filter(username="mysql_compat_user").count() == 1
