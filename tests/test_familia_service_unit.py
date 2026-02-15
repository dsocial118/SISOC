from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from celiaquia.services import familia_service as module

pytestmark = pytest.mark.django_db


class _Chain:
    def __init__(self, data):
        self._data = data

    def select_related(self, *_a):
        return self

    def order_by(self, *_a):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def values_list(self, *_a, **_k):
        return self._data

    def exists(self):
        return bool(self._data)


def test_crear_relacion_responsable_hijo_created_and_update(mocker):
    mocker.patch("celiaquia.services.familia_service.transaction.atomic", return_value=nullcontext())

    rel = SimpleNamespace(
        vinculo="OTRO",
        conviven=False,
        cuidador_principal=False,
        save=mocker.Mock(),
    )
    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.get_or_create",
        return_value=(rel, False),
    )

    out = module.FamiliaService.crear_relacion_responsable_hijo(1, 2)
    assert out["success"] is True
    assert out["relacion_creada"] is False
    assert rel.save.called

    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.get_or_create",
        return_value=(SimpleNamespace(), True),
    )
    out2 = module.FamiliaService.crear_relacion_responsable_hijo(1, 2)
    assert out2["success"] is True
    assert out2["relacion_creada"] is True


def test_crear_relacion_responsable_hijo_error(mocker):
    mocker.patch("celiaquia.services.familia_service.transaction.atomic", return_value=nullcontext())
    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.get_or_create",
        side_effect=RuntimeError("boom"),
    )
    out = module.FamiliaService.crear_relacion_responsable_hijo(1, 2)
    assert out["success"] is False
    assert "boom" in out["error"]


def test_obtener_hijos_responsables_and_fallbacks(mocker):
    h1 = SimpleNamespace(id=10)
    h2 = SimpleNamespace(id=20)
    relaciones = [SimpleNamespace(ciudadano_2=h1), SimpleNamespace(ciudadano_2=h2)]

    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.filter",
        return_value=_Chain(relaciones),
    )
    exp = SimpleNamespace(expediente_ciudadanos=SimpleNamespace(values_list=lambda *a, **k: [20]))
    assert module.FamiliaService.obtener_hijos_a_cargo(1) == [h1, h2]
    assert module.FamiliaService.obtener_hijos_a_cargo(1, expediente=exp) == [h2]

    responsables = [SimpleNamespace(ciudadano_1="r1"), SimpleNamespace(ciudadano_1="r2")]
    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.filter",
        return_value=_Chain(responsables),
    )
    assert module.FamiliaService.obtener_responsables(2) == ["r1", "r2"]


def test_obtener_responsable_es_responsable_ids_y_por_hijo(mocker):
    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.filter",
        return_value=_Chain([SimpleNamespace(ciudadano_1_id=99)]),
    )
    assert module.FamiliaService.obtener_responsable_de_hijo(5) == 99
    assert module.FamiliaService.es_responsable(6) is True

    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.filter",
        return_value=SimpleNamespace(values_list=lambda *a, **k: [1, 2]),
    )
    assert module.FamiliaService.obtener_ids_responsables([1, 2, 3]) == {1, 2}

    rels = [
        SimpleNamespace(ciudadano_2_id=7, ciudadano_1="a"),
        SimpleNamespace(ciudadano_2_id=7, ciudadano_1="b"),
    ]
    mocker.patch(
        "celiaquia.services.familia_service.GrupoFamiliar.objects.filter",
        return_value=_Chain(rels),
    )
    out = module.FamiliaService.obtener_responsables_por_hijo([7])
    assert out == {7: ["a", "b"]}
    assert module.FamiliaService.obtener_responsables_por_hijo([]) == {}


def test_obtener_estructura_familiar_expediente_and_error(mocker):
    class Legajo:
        def __init__(self, cid):
            self.ciudadano_id = cid
            self.ciudadano = SimpleNamespace(id=cid)

    leg_responsable = Legajo(1)
    leg_hijo = Legajo(2)
    exp = SimpleNamespace(
        expediente_ciudadanos=SimpleNamespace(select_related=lambda *_a: [leg_responsable, leg_hijo])
    )

    mocker.patch.object(module.FamiliaService, "obtener_ids_responsables", return_value={1})
    mocker.patch.object(module.FamiliaService, "obtener_hijos_a_cargo", return_value=[SimpleNamespace(id=2)])
    mocker.patch.object(module.FamiliaService, "obtener_responsables", return_value=[SimpleNamespace(id=1)])

    out = module.FamiliaService.obtener_estructura_familiar_expediente(exp)
    assert len(out["responsables"]) == 1
    assert out["hijos_sin_responsable"] == []

    exp_broken = SimpleNamespace(expediente_ciudadanos=SimpleNamespace(select_related=lambda *_a: (_ for _ in ()).throw(RuntimeError("x"))))
    out_err = module.FamiliaService.obtener_estructura_familiar_expediente(exp_broken)
    assert out_err["responsables"] == {}
    assert "error" in out_err
