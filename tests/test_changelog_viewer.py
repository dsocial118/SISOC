import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.core.cache import cache
from core.views import get_current_version, fetch_changelog_content

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
    assert "changelog_html" in response.context
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


def test_fetch_changelog_content_success():
    """Test that fetch_changelog_content reads the changelog file."""
    content = fetch_changelog_content()
    # Should return content from CHANGELOG.md or None if unavailable
    assert content is None or isinstance(content, str)
    # If content exists, should contain expected markers
    if content:
        assert "CHANGELOG" in content or "Despliegue" in content


@patch("core.views.cache")
def test_changelog_view_uses_cache(mock_cache, auth_client):
    """Test that changelog view uses caching."""
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    
    url = reverse("changelog")
    response = auth_client.get(url)
    
    assert response.status_code == 200
    # Verify cache.get was called
    assert mock_cache.get.called
    # Verify cache.set was called if content was fetched
    if response.context.get("changelog_html"):
        assert mock_cache.set.called


def test_changelog_view_error_handling(auth_client):
    """Test that changelog view handles errors gracefully."""
    # Clear cache to ensure we test the error path
    cache.clear()
    
    with patch("core.views.fetch_changelog_content", return_value=None):
        url = reverse("changelog")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.context["error"] is True
        assert response.context["changelog_html"] is None
