from django.contrib.auth.decorators import login_required
from django.urls import path

urlpatterns = [
    path(
        "provincias/proyectos/listar",
        login_required(EDITME.as_view()),
        name="proyectos",
    ),
    path(
        "provincias/proyectos/crear",
        login_required(EDITME.as_view()),
        name="comedor_crear",
    ),
    path(
        "provincias/proyectos/<pk>",
        login_required(EDITME.as_view()),
        name="comedor_detalle",
    ),
    path(
        "provincias/proyectos/<pk>/editar",
        login_required(EDITME.as_view()),
        name="comedor_editar",
    ),
    path(
        "provincias/proyectos/<pk>/eliminar",
        login_required(EDITME.as_view()),
        name="comedor_eliminar",
    ),
]
