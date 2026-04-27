from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect, RelatedFieldWidgetWrapper
from django.test import RequestFactory

from celiaquia.models import ExpedienteCiudadano


class DummyAdminUser:
    is_active = True
    is_staff = True

    def has_perm(self, perm, obj=None):
        return True


def test_expedienteciudadano_admin_uses_autocomplete_for_high_cardinality_foreign_keys():
    model_admin = admin.site._registry[ExpedienteCiudadano]
    request = RequestFactory().get("/admin/celiaquia/expedienteciudadano/1/change/")
    request.user = DummyAdminUser()

    form = model_admin.get_form(request)

    for field_name in ("deleted_by", "expediente", "ciudadano", "subsanacion_usuario"):
        widget = form.base_fields[field_name].widget
        assert isinstance(widget, RelatedFieldWidgetWrapper)
        assert isinstance(widget.widget, AutocompleteSelect)
