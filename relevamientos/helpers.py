from django.contrib import messages
from django.shortcuts import get_object_or_404

from comedores.forms.comedor_form import ReferenteForm
from comedores.models import Comedor
from .form import (
    FuncionamientoPrestacionForm,
    EspacioForm,
    EspacioCocinaForm,
    EspacioPrestacionForm,
    ColaboradoresForm,
    FuenteRecursosForm,
    FuenteComprasForm,
    PrestacionForm,
    AnexoForm,
    PuntosEntregaForm,
)


class RelevamientoFormManager:
    """
    Helper para armar, bindear y validar todos los formularios relacionados a un relevamiento.
    """

    FORM_CLASSES = {
        "funcionamiento_form": FuncionamientoPrestacionForm,
        "espacio_form": EspacioForm,
        "espacio_cocina_form": EspacioCocinaForm,
        "espacio_prestacion_form": EspacioPrestacionForm,
        "colaboradores_form": ColaboradoresForm,
        "recursos_form": FuenteRecursosForm,
        "compras_form": FuenteComprasForm,
        "prestacion_form": PrestacionForm,
        "referente_form": ReferenteForm,
        "anexo_form": AnexoForm,
        "punto_entregas_form": PuntosEntregaForm,
    }

    @classmethod
    def build_forms(cls, post_data=None, instance_map=None):
        """
        post_data: request.POST o None
        instance_map: dict con instancias para forms (para UpdateView)
        """
        forms = {}
        for name, form_class in cls.FORM_CLASSES.items():
            instance = instance_map.get(name) if instance_map else None
            if instance is not None:
                forms[name] = form_class(post_data, instance=instance)
            else:
                forms[name] = form_class(post_data)
        return forms

    @staticmethod
    def get_comedor_context(comedor_pk, extra_fields=None):
        data = get_object_or_404(Comedor.objects.values("id", "nombre"), pk=comedor_pk)
        if extra_fields:
            data.update(extra_fields)
        return data

    @staticmethod
    def validate_forms(forms):
        """
        Valida todos los formularios y retorna un dict con el resultado de cada uno.
        """
        results = {name: form.is_valid() for name, form in forms.items()}
        return results

    @staticmethod
    def all_valid(forms, validation_results=None):
        """
        Retorna True si todos los formularios son válidos. Si se pasa validation_results,
        lo usa en vez de volver a validar.
        """
        if validation_results is not None:
            return all(validation_results.values())
        return all(form.is_valid() for form in forms.values())

    @staticmethod
    def get_errors(forms, validation_results=None):
        """
        Retorna los errores de los formularios inválidos. Si se pasa validation_results,
        lo usa en vez de volver a validar.
        """
        if validation_results is not None:
            return {
                name: forms[name].errors
                for name, valid in validation_results.items()
                if not valid
            }
        return {
            name: form.errors for name, form in forms.items() if not form.is_valid()
        }

    @staticmethod
    def show_form_errors(request, forms, validation_results=None):
        """
        Muestra los errores de los formularios inválidos usando messages.
        """
        errors = RelevamientoFormManager.get_errors(forms, validation_results)
        for form_name, error in errors.items():
            messages.error(request, f"Errores en {form_name}: {error}")
