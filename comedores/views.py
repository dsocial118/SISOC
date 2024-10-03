from typing import Any
from django.contrib import messages
from django.db.models.base import Model
from django.forms import BaseModelForm
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from comedores.forms.comedor_form import ComedorForm, ReferenteForm
from comedores.forms.observacion_form import ObservacionForm
from comedores.forms.relevamiento_form import (
    ColaboradoresForm,
    EspacioCocinaForm,
    EspacioForm,
    EspacioPrestacionForm,
    FuenteComprasForm,
    FuenteRecursosForm,
    FuncionamientoPrestacionForm,
    PrestacionForm,
    RelevamientoForm,
)
from comedores.models import Comedor, Observacion, Prestacion, Relevamiento
from comedores.serializers.comedor_serializer import ComedorSerializer
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer
from comedores.serializers.observacion_serializer import ObservacionSerializer
from comedores.services.comedor_service import ComedorService
from comedores.services.relevamiento_service import RelevamientoService
from usuarios.models import Usuarios


class ComedorListView(ListView):
    model = Comedor
    template_name = "comedor/comedor_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        return ComedorService.get_comedores_filtrados(query)


class ComedorCreateView(CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["referente_form"] = ReferenteForm(
            self.request.POST if self.request.POST else None, prefix="referente"
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():  # Creo y asigno el referente
            self.object = form.save()
            self.object.referente = referente_form.save()
            self.object.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDetailView(DetailView):
    model = Comedor
    template_name = "comedor/comedor_detail.html"
    context_object_name = "comedor"

    def get_object(self, queryset=None):
        return ComedorService.get_comedor_detail_object(self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "relevamientos": Relevamiento.objects.filter(comedor=self.object["id"])
                .values("id", "fecha_visita")
                .order_by("-fecha_visita")[:12],
                "observaciones": Observacion.objects.filter(comedor=self.object["id"])
                .values("id", "fecha")
                .order_by("-fecha")[:12],
            }
        )

        return context


class ComedorUpdateView(UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.object = self.get_object()
        data["referente_form"] = ReferenteForm(
            self.request.POST if self.request.POST else None,
            instance=self.object.referente,
            prefix="referente",
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]

        if referente_form.is_valid():
            self.object = form.save()
            self.object.referente = referente_form.save()
            self.object.save()

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDeleteView(DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")


class RelevamientoCreateView(CreateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento/relevamiento_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = {
            "funcionamiento_form": FuncionamientoPrestacionForm,
            "espacio_form": EspacioForm,
            "espacio_cocina_form": EspacioCocinaForm,
            "espacio_prestacion_form": EspacioPrestacionForm,
            "colaboradores_form": ColaboradoresForm,
            "recursos_form": FuenteRecursosForm,
            "compras_form": FuenteComprasForm,
            "prestacion_form": PrestacionForm,
        }

        for form_name, form_class in forms.items():
            data[form_name] = form_class(
                self.request.POST if self.request.POST else None
            )

        data["comedor"] = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {
            "funcionamiento_form": context["funcionamiento_form"],
            "espacio_form": context["espacio_form"],
            "espacio_cocina_form": context["espacio_cocina_form"],
            "espacio_prestacion_form": context["espacio_prestacion_form"],
            "colaboradores_form": context["colaboradores_form"],
            "recursos_form": context["recursos_form"],
            "compras_form": context["compras_form"],
            "prestacion_form": context["prestacion_form"],
        }

        if all(form.is_valid() for form in forms.values()):
            self.object = RelevamientoService.guardar_relevamiento(
                form, forms, self.request.user.id
            )

            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
            return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDetailView(DetailView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_detail.html"
    context_object_name = "relevamiento"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["relevamiento"]["gas"] = RelevamientoService.generar_string_gas(
            self.get_object()["id"]
        )
        context["prestacion"] = Prestacion.objects.get(pk=self.object["prestacion__id"])

        return context

    def get_object(self, queryset=None) -> Model:
        return RelevamientoService.get_relevamiento_detail_object(self.kwargs["pk"])


class RelevamientoUpdateView(UpdateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento/relevamiento_form.html"
    success_url = reverse_lazy("relevamiento_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = {
            "funcionamiento_form": FuncionamientoPrestacionForm,
            "espacio_form": EspacioForm,
            "espacio_cocina_form": EspacioCocinaForm,
            "espacio_prestacion_form": EspacioPrestacionForm,
            "colaboradores_form": ColaboradoresForm,
            "recursos_form": FuenteRecursosForm,
            "compras_form": FuenteComprasForm,
            "prestacion_form": PrestacionForm,
        }

        for form_name, form_class in forms.items():
            data[form_name] = form_class(
                self.request.POST if self.request.POST else None,
                instance=getattr(
                    self.object, form_name.split("_form", maxsplit=1)[0], None
                ),
            )

        data["comedor"] = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {
            "funcionamiento_form": context["funcionamiento_form"],
            "espacio_form": context["espacio_form"],
            "espacio_cocina_form": context["espacio_cocina_form"],
            "espacio_prestacion_form": context["espacio_prestacion_form"],
            "colaboradores_form": context["colaboradores_form"],
            "recursos_form": context["recursos_form"],
            "compras_form": context["compras_form"],
        }

        if all(form.is_valid() for form in forms.values()):
            self.object = RelevamientoService.guardar_relevamiento(
                form, forms, self.request.user.id
            )

            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
            return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDeleteView(DeleteView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


class ObservacionCreateView(CreateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "comedor": Comedor.objects.values("id", "nombre").get(
                    pk=self.kwargs["comedor_pk"]
                )
            }
        )

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = Usuarios.objects.get(pk=self.request.user.id).usuario
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha = timezone.now()

        self.object = form.save()

        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDetailView(DetailView):
    model = Observacion
    template_name = "observacion/observacion_detail.html"
    context_object_name = "observacion"

    def get_object(self, queryset=None) -> Model:
        return (
            Observacion.objects.prefetch_related("comedor")
            .values(
                "id",
                "fecha",
                "observacion",
                "comedor__id",
                "comedor__nombre",
                "observador",
            )
            .get(pk=self.kwargs["pk"])
        )


class ObservacionUpdateView(UpdateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comedor = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        context.update({"comedor": comedor})

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = Usuarios.objects.get(pk=self.request.user.id).usuario
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha = timezone.now()

        self.object = form.save()

        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDeleteView(DeleteView):
    model = Observacion
    template_name = "observacion/observacion_confirm_delete.html"
    context_object_name = "observacion"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


class ComedorRelevamientoObservacion(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        comedor_data = request.data.get("comedor")
        relevamiento_data = request.data.get("relevamiento")
        observacion_data = request.data.get("observacion")

        try:
            comedor = Comedor.objects.get(
                unique_key=ComedorService.generar_unique_key(comedor_data)
            )
        except Comedor.DoesNotExist:
            comedor_serializer = ComedorSerializer(data=comedor_data).clean()
            if comedor_serializer.is_valid():
                comedor_serializer.save()
                comedor = comedor_serializer.instance
            else:
                return Response(
                    comedor_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
        relevamiento_data["comedor"] = comedor.id
        relevamiento_serializer = RelevamientoSerializer(data=relevamiento_data).clean()
        if relevamiento_serializer.is_valid():
            relevamiento_serializer.save()
        else:
            return Response(
                relevamiento_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        observacion_data["comedor"] = comedor.id
        observacion_serializer = ObservacionSerializer(data=observacion_data).clean()
        if observacion_serializer.is_valid():
            observacion_serializer.save()
        else:
            return Response(
                observacion_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "comedor": model_to_dict(comedor),
                "relevamiento": relevamiento_serializer.data,
                "observacion": observacion_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
