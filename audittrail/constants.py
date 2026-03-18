"""
Constantes y helpers de modelos auditables.

La metadata vive en una única fuente para evitar drift entre:
- opciones/allowlist de vistas
- registro real en django-auditlog
"""

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from typing import Callable

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist


def _import_model(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


@dataclass(frozen=True)
class TrackedModelDefinition:
    """Definición canónica de un modelo auditable."""

    label: str
    model_getter: Callable
    excluded_fields: tuple[str, ...] = ()
    optional_excluded_fields: tuple[str, ...] = ()

    def get_model(self):
        return self.model_getter()

    def get_model_key(self):
        model = self.get_model()
        return model._meta.app_label, model._meta.model_name

    def get_excluded_fields(self):
        model = self.get_model()
        fields = list(self.excluded_fields)
        for field_name in self.optional_excluded_fields:
            try:
                model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            fields.append(field_name)
        return fields


def _model_getter(dotted_path: str):
    return lambda: _import_model(dotted_path)


@lru_cache(maxsize=1)
def get_tracked_model_definitions():
    """
    Devuelve la definición canónica de modelos auditables.
    """
    return (
        TrackedModelDefinition(
            label="Comedor",
            model_getter=_model_getter("comedores.models.Comedor"),
            excluded_fields=("fecha_creacion", "fecha_actualizacion"),
        ),
        TrackedModelDefinition(
            label="Centro de Infancia",
            model_getter=_model_getter("centrodeinfancia.models.CentroDeInfancia"),
            excluded_fields=("fecha_creacion",),
        ),
        TrackedModelDefinition(
            label="Formulario CDI",
            model_getter=_model_getter("centrodeinfancia.models.FormularioCDI"),
            excluded_fields=("created_at", "updated_at"),
        ),
        TrackedModelDefinition(
            label="Relevamiento",
            model_getter=_model_getter("relevamientos.models.Relevamiento"),
            excluded_fields=("fecha_creacion",),
        ),
        TrackedModelDefinition(
            label="Ciudadano",
            model_getter=_model_getter("ciudadanos.models.Ciudadano"),
            excluded_fields=("creado", "modificado"),
        ),
        TrackedModelDefinition(
            label="Nómina",
            model_getter=_model_getter("comedores.models.Nomina"),
            excluded_fields=("fecha",),
        ),
        TrackedModelDefinition(
            label="Organización",
            model_getter=_model_getter("organizaciones.models.Organizacion"),
            excluded_fields=("fecha_creacion",),
        ),
        TrackedModelDefinition(
            label="Usuario",
            model_getter=get_user_model,
            excluded_fields=("password",),
            optional_excluded_fields=("last_login",),
        ),
    )


def get_tracked_models():
    """
    Lista de tuplas (app_label, model_name, label) para UI/allowlist.
    """
    return [
        (*definition.get_model_key(), definition.label)
        for definition in get_tracked_model_definitions()
    ]


def get_tracked_model_allowlist():
    """
    Mapa (app_label, model_name) -> definición.
    """
    return {
        definition.get_model_key(): definition
        for definition in get_tracked_model_definitions()
    }


def is_tracked_model(app_label: str, model_name: str) -> bool:
    """
    Verifica si un par app/model está habilitado para auditoría.
    """
    return (app_label, model_name) in get_tracked_model_allowlist()


# Compatibilidad hacia atrás: código/tests existentes importan TRACKED_MODELS.
TRACKED_MODELS = get_tracked_models()


def tracked_model_choices(include_blank: bool = True):
    """
    Devuelve choices listos para formularios (app.model -> etiqueta amigable).
    """
    choices = []
    if include_blank:
        choices.append(("", "Todos los modelos"))
    choices.extend(
        (f"{app}.{model}", label) for app, model, label in get_tracked_models()
    )
    return choices
