import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_voucher_admin_add_view_no_500(auth_client):
    response = auth_client.get(reverse("admin:VAT_voucher_add"))

    assert response.status_code == 200
