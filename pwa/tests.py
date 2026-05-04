from django.test import Client
from types import SimpleNamespace

from pwa.services import nomina_service


def test_pwa_health_endpoint_returns_ok():
    client = Client()
    response = client.get("/api/pwa/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_build_nomina_link_fields_uses_direct_comedor_for_programs_without_admision(
    monkeypatch,
):
    fake_comedor = SimpleNamespace(id=12, programa=SimpleNamespace(id=3))

    class FakeQS:
        def filter(self, **kwargs):
            assert kwargs == {"pk": 12}
            return self

        def first(self):
            return fake_comedor

    class FakeObjects:
        def select_related(self, *args):
            assert args == ("programa",)
            return FakeQS()

    class FakeComedor:
        objects = FakeObjects()

    monkeypatch.setattr(nomina_service, "Comedor", FakeComedor)
    monkeypatch.setattr(
        nomina_service,
        "comedor_usa_admision_para_nomina",
        lambda comedor: False,
    )

    result = nomina_service._build_nomina_link_fields(comedor_id=12)

    assert result["admision"] is None
    assert result["comedor"] is fake_comedor


def test_build_nomina_link_fields_uses_admision_for_programs_with_admision(
    monkeypatch,
):
    fake_comedor = SimpleNamespace(id=44, programa=SimpleNamespace(id=2))
    fake_admision = SimpleNamespace(id=99)

    class FakeQS:
        def filter(self, **kwargs):
            assert kwargs == {"pk": 44}
            return self

        def first(self):
            return fake_comedor

    class FakeObjects:
        def select_related(self, *args):
            assert args == ("programa",)
            return FakeQS()

    class FakeComedor:
        objects = FakeObjects()

    monkeypatch.setattr(nomina_service, "Comedor", FakeComedor)
    monkeypatch.setattr(
        nomina_service,
        "comedor_usa_admision_para_nomina",
        lambda comedor: True,
    )
    monkeypatch.setattr(
        nomina_service,
        "_resolve_admision_para_comedor",
        lambda comedor_id: fake_admision,
    )

    result = nomina_service._build_nomina_link_fields(comedor_id=44)

    assert result["admision"] is fake_admision
    assert result["comedor"] is None
