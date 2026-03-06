"""Tests unitarios para sync_comedores_gestionar."""

import pytest
from django.core.management import call_command
from django.test import override_settings


pytestmark = pytest.mark.django_db


@override_settings(GESTIONAR_INTEGRATION_ENABLED=False)
def test_sync_comedores_command_is_blocked_outside_production(mocker):
    count_mock = mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.Comedor.objects.all"
    )
    send_mock = mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.requests.post"
    )

    call_command("sync_comedores_gestionar", verbosity=0)

    count_mock.assert_not_called()
    send_mock.assert_not_called()
