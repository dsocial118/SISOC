"""
Tests for CSV export functionality
"""

import csv
from datetime import datetime, date
from io import StringIO
import pytest
from django.contrib.auth.models import User, Group
from django.test import RequestFactory
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
