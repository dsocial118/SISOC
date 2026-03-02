import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="testpass",
    )
