import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.importacion_service import _tipo_doc_cuit
from ciudadanos.models import TipoDocumento


@pytest.mark.django_db
class TestExpedienteService:
    def test_create_expediente_persists_numero_expediente(self):
        user = get_user_model().objects.create_user(username="provincia", password="secret")

        expediente = ExpedienteService.create_expediente(
            usuario_provincia=user,
            datos_metadatos={"numero_expediente": "ABC-123"},
            excel_masivo=None,
        )

        expediente.refresh_from_db()
        assert expediente.numero_expediente == "ABC-123"


@pytest.mark.django_db
class TestImportacionService:
    def test_tipo_doc_cuit_lookup_requires_configured_entry(self):
        _tipo_doc_cuit.cache_clear()

        with pytest.raises(ValidationError):
            _tipo_doc_cuit()

        cuit = TipoDocumento.objects.create(tipo="CUIT")

        _tipo_doc_cuit.cache_clear()
        assert _tipo_doc_cuit() == cuit.id
