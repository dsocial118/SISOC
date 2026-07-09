"""
Tests for CSV export functionality
"""

import csv
from datetime import datetime, date
from io import StringIO
import pytest
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.views.generic import View
from core.mixins import CSVExportMixin


class SimpleExportView(CSVExportMixin, View):
    """Simple test view for CSV export"""

    export_filename = "listado_test.csv"

    def get_export_columns(self):
        return [
            ("ID", "id"),
            ("Name", "name"),
            ("Date", "created_at"),
        ]


def _grant_permission(user, app_label, codename):
    permission = Permission.objects.get(
        content_type__app_label=app_label,
        codename=codename,
    )
    user.user_permissions.add(permission)
    return User.objects.get(pk=user.pk)


def _grant_role_permission(user, codename, name):
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults={"name": name},
    )
    user.user_permissions.add(permission)
    return User.objects.get(pk=user.pk)


def _grant_export_role(user):
    return _grant_role_permission(user, "role_exportar_a_csv", "Exportar a csv")


def _grant_admin_role(user):
    return _grant_role_permission(user, "role_admin", "Admin")


@pytest.mark.django_db
class TestCSVExportMixin:
    """Test suite for CSVExportMixin"""

    def test_filename_format(self):
        """Test that filename follows the correct format: exportacion_[module]_[YYYYMMDD_HHMM].csv"""
        view = SimpleExportView()
        view.export_filename = "listado_comedores.csv"

        filename = view.get_export_filename()

        # Check format
        assert filename.startswith("exportacion_comedores_")
        assert filename.endswith(".csv")

        # Extract timestamp part
        parts = filename.split("_")
        assert len(parts) >= 3  # exportacion, module, timestamp (YYYYMMDD, HHMM)

        # Verify timestamp format YYYYMMDD_HHMM
        timestamp_parts = filename.replace("exportacion_comedores_", "").replace(
            ".csv", ""
        )
        assert len(timestamp_parts) == 13  # YYYYMMDD_HHMM = 13 chars
        assert timestamp_parts[8] == "_"  # underscore separator

    def test_date_format_datetime(self):
        """Test that datetime values are formatted as YYYY-MM-DD HH:MM:SS"""
        view = SimpleExportView()

        test_datetime = datetime(2025, 1, 15, 14, 30, 45)
        result = view.resolve_field({"created_at": test_datetime}, "created_at")

        assert result == "2025-01-15 14:30:45"

    def test_date_format_date_only(self):
        """Test that date values are formatted as YYYY-MM-DD 00:00:00"""
        view = SimpleExportView()

        test_date = date(2025, 1, 15)
        result = view.resolve_field({"created_at": test_date}, "created_at")

        assert result == "2025-01-15 00:00:00"

    def test_csv_delimiter(self):
        """Test that CSV uses semicolon as delimiter"""
        factory = RequestFactory()
        request = factory.get("/export/")

        # Create user with export permission
        user = User.objects.create_user(username="testuser", password="test123")
        user.is_superuser = True
        request.user = user

        # Create view instance
        view = SimpleExportView()
        view.request = request

        # Mock data
        test_data = [
            {"id": 1, "name": "Test 1", "created_at": date(2025, 1, 15)},
            {"id": 2, "name": "Test 2", "created_at": date(2025, 1, 16)},
        ]

        # Export to CSV
        response = view.export_csv(test_data)

        # Read response content
        content = b"".join(response.streaming_content).decode("utf-8")

        # Check that semicolons are used
        assert ";" in content
        assert "," not in content  # No commas as delimiters

        # Parse CSV with semicolon delimiter
        reader = csv.DictReader(StringIO(content), delimiter=";")
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["ID"] == "1"
        assert rows[0]["Name"] == "Test 1"
        assert rows[0]["Date"] == "2025-01-15 00:00:00"

    def test_permission_check(self):
        """Test that export requires proper permissions"""
        factory = RequestFactory()
        request = factory.get("/export/")

        # User without permission
        user = User.objects.create_user(username="testuser", password="test123")
        request.user = user

        view = SimpleExportView()
        view.request = request

        # Should raise PermissionDenied
        from django.core.exceptions import PermissionDenied

        with pytest.raises(PermissionDenied):
            view.export_csv([])

    def test_permission_with_group(self):
        """Test that export works with correct group"""
        factory = RequestFactory()
        request = factory.get("/export/")

        # Create user and group
        user = User.objects.create_user(username="testuser", password="test123")
        export_group = Group.objects.create(name="Exportar a csv")
        user.groups.add(export_group)
        request.user = user

        view = SimpleExportView()
        view.request = request

        # Should succeed
        response = view.export_csv([])
        assert response.status_code == 200


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_export_rejects_anonymous_user(client):
    response = client.get(reverse("comedor_export"))

    assert response.status_code == 403
    assert "Content-Disposition" not in response


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_export_rejects_list_permission_without_export_permission(client):
    user = User.objects.create_user(username="comedor_export_list")
    user = _grant_permission(user, "admisiones", "view_admision")

    client.force_login(user)
    response = client.get(reverse("comedor_export"))

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_export_rejects_export_role_without_list_permission(client):
    user = User.objects.create_user(username="comedor_export_only")
    user = _grant_export_role(user)

    client.force_login(user)
    response = client.get(reverse("comedor_export"))

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_export_allows_user_with_list_and_export_permissions(client):
    user = User.objects.create_user(username="comedor_export_both")
    user = _grant_permission(user, "admisiones", "view_admision")
    user = _grant_export_role(user)

    client.force_login(user)
    response = client.get(reverse("comedor_export"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith(
        'attachment; filename="exportacion_comedores_'
    )


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_export_allows_admin_role_without_explicit_export_pair(client):
    user = User.objects.create_user(username="comedor_export_admin")
    user = _grant_admin_role(user)

    client.force_login(user)
    response = client.get(reverse("comedor_export"))

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_list_shows_export_button_with_list_and_export_permissions(client):
    user = User.objects.create_user(username="comedor_list_export_button")
    user = _grant_permission(user, "admisiones", "view_admision")
    user = _grant_export_role(user)

    client.force_login(user)
    response = client.get(reverse("comedores"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "btn-export-csv" in content
    assert reverse("comedor_export") in content


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="config.urls")
def test_comedor_list_hides_export_button_with_list_permission_only(client):
    user = User.objects.create_user(username="comedor_list_only_button")
    user = _grant_permission(user, "admisiones", "view_admision")

    client.force_login(user)
    response = client.get(reverse("comedores"))

    assert response.status_code == 200
    assert "btn-export-csv" not in response.content.decode()
