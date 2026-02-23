"""Tests for test changelog viewer."""

from unittest.mock import patch
import pytest
from django.urls import reverse
from django.core.cache import cache
from core.views import get_current_version, fetch_changelog_content, parse_changelog_versions

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


def test_changelog_view_requires_authentication(client):
    """Test that changelog view requires authentication."""
    url = reverse("changelog")
    response = client.get(url)
    # Should redirect to login
    assert response.status_code == 302
    # Application redirects to root path with next parameter
    assert "/?next=" in response.url or "/login" in response.url


def test_changelog_view_authenticated_success(auth_client):
    """Test that authenticated users can access changelog view."""
    url = reverse("changelog")
    response = auth_client.get(url)
    assert response.status_code == 200
    assert "versions" in response.context
    assert "current_version" in response.context


def test_get_current_version():
    """Test that get_current_version extracts version from CHANGELOG.md."""
    version = get_current_version()
    # Should return a version string in format YYYY.MM.DD or "Desconocida"
    assert version is not None
    assert isinstance(version, str)
    # If CHANGELOG.md exists and is properly formatted, should match pattern
    if version != "Desconocida":
        assert len(version.split(".")) == 3


def test_parse_changelog_versions():
    """Test that parse_changelog_versions splits content into per-version blocks."""
    sample = (
        "## Despliegue: 2026.02.03\n### Added\n- Feature A\n\n"
        "## Despliegue: 2026.01.23\n### Fixed\n- Bug B\n"
    )
    versions = parse_changelog_versions(sample)
    assert len(versions) == 2
    assert versions[0]["version"] == "2026.02.03"
    assert versions[1]["version"] == "2026.01.23"
    # The "## Despliegue:" header should not appear in the rendered HTML
    assert "Despliegue" not in versions[0]["html"]
    # Content items should be present
    assert "Feature A" in versions[0]["html"]
    assert "Bug B" in versions[1]["html"]


def test_fetch_changelog_content_success():
    """Test that fetch_changelog_content reads the changelog file."""
    content = fetch_changelog_content()
    # Should return content from CHANGELOG.md or None if unavailable
    assert content is None or isinstance(content, str)
    # If content exists, should contain expected markers
    if content:
        assert "CHANGELOG" in content or "Despliegue" in content


def test_changelog_view_uses_cache(auth_client):
    """Test that changelog view uses caching."""
    url = reverse("changelog")

    # First request - should fetch from file and cache
    cache.clear()
    response1 = auth_client.get(url)
    assert response1.status_code == 200

    # Second request - should use cache
    with patch("core.views.fetch_changelog_content") as mock_fetch:
        response2 = auth_client.get(url)
        assert response2.status_code == 200
        # fetch_changelog_content should not be called if cache is hit
        mock_fetch.assert_not_called()


def test_changelog_view_error_handling(auth_client):
    """Test that changelog view handles errors gracefully."""
    # Clear cache to ensure we test the error path
    cache.clear()

    with patch("core.views.fetch_changelog_content", return_value=None):
        url = reverse("changelog")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.context["error"] is True
        assert response.context["versions"] is None


def test_fetch_changelog_github_fallback():
    """Test that fetch_changelog_content falls back to GitHub when local file is missing."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = "# Test changelog content"
            mock_response.raise_for_status.return_value = None

            content = fetch_changelog_content()

            # Should have attempted to call GitHub
            mock_get.assert_called_once()
            assert "Test changelog content" in content


def test_get_current_version_github_fallback():
    """Test that get_current_version falls back to GitHub when local file is missing."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = "## Despliegue: 2025.01.01\nTest content"
            mock_response.raise_for_status.return_value = None

            version = get_current_version()

            # Should have attempted to call GitHub
            mock_get.assert_called_once()
            assert version == "2025.01.01"
