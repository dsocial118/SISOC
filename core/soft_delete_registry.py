"""Registry of models migrated to soft-delete in the big-bang rollout."""

from django.apps import apps

# app_label.ModelName
SOFT_DELETE_MODEL_KEYS = [
    "admisiones.ArchivoAdmision",
    "relevamientos.Relevamiento",
    "centrodeinfancia.CentroDeInfancia",
    "centrodeinfancia.NominaCentroInfancia",
    "centrodeinfancia.IntervencionCentroInfancia",
    "duplas.Dupla",
    "comedores.Comedor",
    "comedores.Nomina",
    "comedores.Observacion",
    "intervenciones.Intervencion",
    "expedientespagos.ExpedientePago",
    "organizaciones.Organizacion",
    "organizaciones.Firmante",
    "organizaciones.Aval",
    "centrodefamilia.Centro",
    "centrodefamilia.Categoria",
    "centrodefamilia.Actividad",
    "centrodefamilia.ActividadCentro",
    "centrodefamilia.ParticipanteActividad",
    "centrodefamilia.Beneficiario",
    "centrodefamilia.Responsable",
    "centrodefamilia.BeneficiarioResponsable",
    "rendicioncuentasmensual.RendicionCuentaMensual",
    "rendicioncuentasmensual.DocumentacionAdjunta",
    "ciudadanos.Ciudadano",
    "ciudadanos.GrupoFamiliar",
    "celiaquia.AsignacionTecnico",
    "celiaquia.ExpedienteCiudadano",
    "celiaquia.RegistroErroneo",
]


def iter_soft_delete_models():
    """Yield registered soft-delete models that are currently available."""
    for key in SOFT_DELETE_MODEL_KEYS:
        app_label, model_name = key.split(".", 1)
        model = apps.get_model(app_label, model_name)
        if model is not None:
            yield model


def get_soft_delete_model_choices():
    """Build UI-friendly choices for Trash listing."""
    choices = []
    for model in iter_soft_delete_models():
        key = f"{model._meta.app_label}.{model.__name__}"
        label = f"{model._meta.verbose_name_plural.title()} ({model._meta.app_label})"
        choices.append((key, label))
    return sorted(choices, key=lambda item: item[1].lower())

