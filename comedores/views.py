import logging
import os
from typing import Any
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.conf import settings
from django.db.models.base import Model
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)


from ciudadanos.models import CiudadanoPrograma, HistorialCiudadanoProgramas
from comedores.forms.comedor_form import (
    ComedorForm,
    ReferenteForm,
    NominaForm,
)
from comedores.forms.observacion_form import ObservacionForm
from comedores.models import (
    Comedor,
    ImagenComedor,
    Observacion,
    Nomina,
)

from comedores.services.comedor_service import ComedorService
from relevamientos.service import RelevamientoService

from duplas.dupla_service import DuplaService
from rendicioncuentasmensual.services import RendicionCuentaMensualService


logger = logging.getLogger("django")


@require_POST
def relevamiento_crear_editar_ajax(request, pk):
    try:
        if "territorial" in request.POST:
            relevamiento = RelevamientoService.create_pendiente(request, pk)
            messages.success(request, "Relevamiento territorial creado correctamente.")
        elif "territorial_editar" in request.POST:
            relevamiento = RelevamientoService.update_territorial(request)
            messages.success(
                request, "Relevamiento territorial actualizado correctamente."
            )
        else:
            messages.error(request, "Acción no reconocida.")
            return redirect("comedor_detalle", pk=pk)

        return redirect(
            "relevamiento_detalle",
            pk=relevamiento.pk,
            comedor_pk=relevamiento.comedor.pk,
        )
    except Exception as e:
        logger.error(
            "Error al procesar relevamiento para comedor %s: %s",
            pk,
            e,
            exc_info=True,
        )
        messages.error(
            request, "Hubo un error al guardar el relevamiento. Intenta de nuevo."
        )
        return redirect("comedor_detalle", pk=pk)


@method_decorator(csrf_exempt, name="dispatch")
class NominaDetailView(TemplateView):
    template_name = "comedor/nomina_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_pk = self.kwargs["pk"]
        page = self.request.GET.get("page", 1)

        page_obj, nomina_m, nomina_f, espera, total = ComedorService.detalle_de_nomina(
            comedor_pk, page
        )

        comedor = ComedorService.get_comedor(comedor_pk)

        context.update(
            {
                "nomina": page_obj,
                "nominaM": nomina_m,
                "nominaF": nomina_f,
                "espera": espera,
                "cantidad_nomina": total,
                "object": comedor,
            }
        )
        return context


class NominaCreateView(CreateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        user = self.request.user
        ciudadano = form.cleaned_data["ciudadano"]
        comedor_id = self.kwargs["pk"]

        form.instance.comedor_id = comedor_id

        response = super().form_valid(form)

        created = CiudadanoPrograma.objects.get_or_create(
            ciudadano=ciudadano, programas_id=2, defaults={"creado_por": user}
        )

        if created:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=2, ciudadano=ciudadano, accion="agregado", usuario=user
            )

        messages.success(self.request, "Persona añadida correctamente a la nómina.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = ComedorService.get_comedor(self.kwargs["pk"])
        return context


class NominaUpdateView(UpdateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"
    pk_url_kwarg = "pk2"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        messages.success(self.request, "Registro de nómina actualizado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = ComedorService.get_comedor(self.kwargs["pk"])
        return context


class NominaDeleteView(DeleteView):
    model = Nomina
    template_name = "comedor/nomina_confirm_delete.html"
    pk_url_kwarg = "pk2"

    def get_success_url(self):
        return reverse_lazy("nomina_ver", kwargs={"pk": self.kwargs["pk"]})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Registro de nómina eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


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
            self.request.POST or None, prefix="referente"
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")

        if referente_form.is_valid():
            self.object = form.save(commit=False)
            self.object.referente = referente_form.save()
            self.object.save()
            for imagen in imagenes:
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDetailView(DetailView):
    model = Comedor
    template_name = "comedor/comedor_detail.html"
    context_object_name = "comedor"

    def get_object(self, queryset=None):
        return ComedorService.get_comedor_detail_object(self.kwargs["pk"])

    def _get_presupuestos_data(self):
        """Obtiene datos de presupuestos usando cache y datos prefetched cuando sea posible."""
        if (
            hasattr(self.object, "relevamientos_optimized")
            and self.object.relevamientos_optimized
        ):
            cache_key = f"presupuestos_comedor_{self.object.id}"
            cached_presupuestos = cache.get(cache_key)

            if cached_presupuestos:
                presupuestos_tuple = cached_presupuestos
            else:
                presupuestos_tuple = ComedorService.get_presupuestos(
                    self.object.id,
                    relevamientos_prefetched=self.object.relevamientos_optimized,
                )
                cache.set(
                    cache_key,
                    presupuestos_tuple,
                    getattr(settings, "COMEDOR_CACHE_TIMEOUT", 300),
                )
        else:
            presupuestos_tuple = ComedorService.get_presupuestos(self.object.id)

        # Desempaquetar la tupla y crear diccionario
        (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
        ) = presupuestos_tuple

        return {
            "count_beneficiarios": count_beneficiarios,
            "presupuesto_desayuno": valor_desayuno,
            "presupuesto_almuerzo": valor_almuerzo,
            "presupuesto_merienda": valor_merienda,
            "presupuesto_cena": valor_cena,
        }

    def _get_relaciones_optimizadas(self):
        """Obtiene datos de relaciones usando prefetch cuando sea posible."""
        # Optimización: Usar rendiciones prefetched en lugar de query adicional
        rendiciones_mensuales = (
            len(self.object.rendiciones_optimized)
            if hasattr(self.object, "rendiciones_optimized")
            else RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(
                self.object
            )
        )

        # Optimización: Usar relaciones prefetched en lugar de queries adicionales
        relevamientos = (
            self.object.relevamientos_optimized[:1]
            if hasattr(self.object, "relevamientos_optimized")
            else []
        )
        observaciones = (
            self.object.observaciones_optimized
            if hasattr(self.object, "observaciones_optimized")
            else []
        )

        # Optimización: Contar relevamientos usando los prefetched o query única si es necesario
        count_relevamientos = (
            len(self.object.relevamientos_optimized)
            if hasattr(self.object, "relevamientos_optimized")
            else self.object.relevamiento_set.count()
        )

        # Optimización: Usar clasificación prefetched
        comedor_categoria = (
            self.object.clasificaciones_optimized[0]
            if hasattr(self.object, "clasificaciones_optimized")
            and self.object.clasificaciones_optimized
            else None
        )

        # Optimización: Usar admisión prefetched
        admision = (
            self.object.admisiones_optimized[0]
            if hasattr(self.object, "admisiones_optimized")
            and self.object.admisiones_optimized
            else None
        )

        # Optimización: Usar imágenes prefetched en lugar de .values()
        imagenes = (
            [{"imagen": img.imagen} for img in self.object.imagenes_optimized]
            if hasattr(self.object, "imagenes_optimized")
            else list(self.object.imagenes.values("imagen"))
        )

        return {
            "relevamientos": relevamientos,
            "observaciones": observaciones,
            "count_relevamientos": count_relevamientos,
            "imagenes": imagenes,
            "comedor_categoria": comedor_categoria,
            "rendicion_cuentas_final_activo": rendiciones_mensuales >= 5,
            "admision": admision,
        }

    def _get_environment_config(self):
        """Obtiene configuración del entorno."""
        return {
            "GESTIONAR_API_KEY": os.getenv("GESTIONAR_API_KEY"),
            "GESTIONAR_API_CREAR_COMEDOR": os.getenv("GESTIONAR_API_CREAR_COMEDOR"),
        }

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Obtener datos de presupuestos
        presupuestos_data = self._get_presupuestos_data()

        # Obtener datos optimizados de relaciones
        relaciones_data = self._get_relaciones_optimizadas()

        # Obtener configuración del entorno
        env_config = self._get_environment_config()

        # Combinar todos los datos en el contexto
        context.update({**presupuestos_data, **relaciones_data, **env_config})

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        is_new_relevamiento = "territorial" in request.POST
        is_edit_relevamiento = "territorial_editar" in request.POST

        if is_new_relevamiento or is_edit_relevamiento:
            try:
                relevamiento = None
                if is_new_relevamiento:
                    relevamiento = RelevamientoService.create_pendiente(
                        request, self.object.id
                    )

                elif is_edit_relevamiento:
                    relevamiento = RelevamientoService.update_territorial(request)

                return redirect(
                    reverse(
                        "relevamiento_detalle",
                        kwargs={
                            "pk": relevamiento.pk,
                            "comedor_pk": relevamiento.comedor.pk,
                        },
                    )
                )
            except Exception as e:
                messages.error(request, f"Error al crear el relevamiento: {e}")
                return redirect("comedor_detalle", pk=self.object.id)

        else:
            return redirect("comedor_detalle", pk=self.object.id)


class AsignarDuplaListView(ListView):
    model = Comedor
    template_name = "comedor/asignar_dupla_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        duplas = DuplaService.get_duplas_by_estado_activo()
        data["comedor"] = comedor
        data["duplas"] = duplas
        return data

    def post(self, request, *args, **kwargs):
        dupla_id = request.POST.get("dupla_id")
        comedor_id = self.kwargs["pk"]

        if dupla_id:
            try:
                ComedorService.asignar_dupla_a_comedor(dupla_id, comedor_id)
                messages.success(request, "Dupla asignada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al asignar la dupla: {e}")
        else:
            messages.error(request, "No se seleccionó ninguna dupla.")

        return redirect("comedor_detalle", pk=comedor_id)


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
        data["imagenes_borrar"] = ImagenComedor.objects.filter(
            comedor=self.object.pk
        ).values("id", "imagen")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")
        dupla_original = self.object.dupla

        if referente_form.is_valid():
            self.object = form.save(commit=False)
            self.object.dupla = dupla_original
            self.object.referente = referente_form.save()
            self.object.save()

            ComedorService.borrar_imagenes(self.request.POST)

            for imagen in imagenes:
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDeleteView(DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")


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
        usuario = User.objects.get(pk=self.request.user.id)
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()

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
                "fecha_visita",
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
        usuario = User.objects.get(pk=self.request.user.id)
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()

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
