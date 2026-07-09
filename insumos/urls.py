from django.urls import path

from core.decorators import permissions_any_required

from .views import (
    InsumoCategoriaCreateView,
    InsumoCategoriaDeleteView,
    InsumoCategoriaListView,
    InsumoCategoriaUpdateView,
    InsumoCreateView,
    InsumoDeleteView,
    InsumoDescargarView,
    InsumoListView,
    InsumoUpdateView,
)

urlpatterns = [
    path(
        "insumos/",
        permissions_any_required(["insumos.view_insumo"])(InsumoListView.as_view()),
        name="insumos_listar",
    ),
    path(
        "insumos/crear",
        permissions_any_required(["insumos.add_insumo"])(InsumoCreateView.as_view()),
        name="insumos_crear",
    ),
    path(
        "insumos/<int:pk>/editar",
        permissions_any_required(["insumos.change_insumo"])(InsumoUpdateView.as_view()),
        name="insumos_editar",
    ),
    path(
        "insumos/<int:pk>/eliminar",
        permissions_any_required(["insumos.delete_insumo"])(InsumoDeleteView.as_view()),
        name="insumos_eliminar",
    ),
    path(
        "insumos/<int:pk>/descargar",
        permissions_any_required(["insumos.view_insumo"])(
            InsumoDescargarView.as_view()
        ),
        name="insumos_descargar",
    ),
    path(
        "insumos/categorias/",
        permissions_any_required(["insumos.view_insumocategoria"])(
            InsumoCategoriaListView.as_view()
        ),
        name="insumos_categorias_listar",
    ),
    path(
        "insumos/categorias/crear",
        permissions_any_required(["insumos.add_insumocategoria"])(
            InsumoCategoriaCreateView.as_view()
        ),
        name="insumos_categorias_crear",
    ),
    path(
        "insumos/categorias/<int:pk>/editar",
        permissions_any_required(["insumos.change_insumocategoria"])(
            InsumoCategoriaUpdateView.as_view()
        ),
        name="insumos_categorias_editar",
    ),
    path(
        "insumos/categorias/<int:pk>/eliminar",
        permissions_any_required(["insumos.delete_insumocategoria"])(
            InsumoCategoriaDeleteView.as_view()
        ),
        name="insumos_categorias_eliminar",
    ),
]
