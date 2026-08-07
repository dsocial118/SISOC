from types import SimpleNamespace

from django.test import RequestFactory
from django.urls import resolve

from organizaciones import views as module


class _QS:
    def __init__(self, items):
        self.items = items

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, **kwargs):
        if "nombre__icontains" in kwargs:
            term = kwargs["nombre__icontains"].lower()
            return _QS([item for item in self.items if term in item.nombre.lower()])
        return self

    def count(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


def test_load_organizaciones_paginado(mocker):
    request = RequestFactory().get(
        "/ajax/load-organizaciones/", {"q": "org", "page": "1"}
    )
    request.user = SimpleNamespace(id=1, is_authenticated=True)
    items = [
        SimpleNamespace(id=1, nombre="Organizacion A"),
        SimpleNamespace(id=2, nombre="Otra"),
    ]
    mocker.patch(
        "organizaciones.views.Organizacion.objects.all", return_value=_QS(items)
    )

    response = module.load_organizaciones(request)

    assert response.status_code == 200


def test_load_organizaciones_conserva_la_ruta_y_nombre_publicos():
    match = resolve("/ajax/load-organizaciones/")

    assert match.url_name == "ajax_load_organizaciones"
    assert match.func == module.load_organizaciones
