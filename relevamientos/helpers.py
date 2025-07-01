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
        data = Comedor.objects.values("id", "nombre").get(pk=comedor_pk)
        if extra_fields:
            data.update(extra_fields)
        return data

    @staticmethod
    def all_valid(forms):
        return all(form.is_valid() for form in forms.values())

    @staticmethod
    def get_errors(forms):
        return {
            name: form.errors for name, form in forms.items() if not form.is_valid()
        }
