import logging
import re
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum
from django.views.generic import ListView, CreateView, DetailView, View
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ciudadanos.models import Ciudadano
from VAT.models import VoucherParametria, Voucher
from VAT.forms import VoucherParametriaForm
from VAT.services.voucher_service.impl import VoucherService

logger = logging.getLogger("django")

# Resultado posibles al intentar asignar un voucher desde una parametría
_CREADO = "creado"
_REACTIVADO = "reactivado"
_YA_ACTIVO = "ya_activo"
_NO_ENCONTRADO = "no_encontrado"
_ERROR = "error"


def _asignar_desde_parametria(ciudadano, parametria, usuario):
    """
    Lógica centralizada de asignación/reactivación de voucher desde una parametría.

    Retorna un string con el resultado: _CREADO, _REACTIVADO, _YA_ACTIVO, _ERROR.

    Conducta:
    - Si ya tiene voucher ACTIVO para ese programa → no hace nada (_YA_ACTIVO).
    - Si tiene voucher AGOTADO o VENCIDO → lo recarga/reinicia según parametria.renovacion_tipo.
    - Si no tiene ninguno (o solo cancelados) → crea uno nuevo.
    """
    # Voucher activo ya existente
    if Voucher.objects.filter(
        ciudadano=ciudadano,
        programa=parametria.programa,
        estado="activo",
    ).exists():
        return _YA_ACTIVO

    # Voucher agotado o vencido reactivable
    voucher_previo = (
        Voucher.objects.filter(
            ciudadano=ciudadano,
            programa=parametria.programa,
            estado__in=["agotado", "vencido"],
        )
        .order_by("-fecha_asignacion")
        .first()
    )

    cantidad = parametria.cantidad_renovacion or parametria.cantidad_inicial
    reiniciar = parametria.renovacion_tipo == "reinicia"

    if voucher_previo:
        with transaction.atomic():
            ok, _ = VoucherService.recargar_voucher(
                voucher=voucher_previo,
                cantidad=cantidad,
                motivo="automatica",
                usuario=usuario,
                reiniciar=reiniciar,
            )
            # Actualizar vencimiento y parametria en el mismo atomic para evitar estado inconsistente
            voucher_previo.fecha_vencimiento = parametria.fecha_vencimiento
            voucher_previo.parametria = parametria
            voucher_previo.save(update_fields=["fecha_vencimiento", "parametria", "fecha_modificacion"])
        return _REACTIVADO if ok else _ERROR

    # No existe ninguno → crear
    VoucherService.crear_voucher(
        ciudadano_id=ciudadano.id,
        programa_id=parametria.programa_id,
        cantidad=parametria.cantidad_inicial,
        fecha_vencimiento=parametria.fecha_vencimiento,
        usuario=usuario,
        parametria=parametria,
    )
    return _CREADO


class VoucherParametriaListView(LoginRequiredMixin, ListView):
    model = VoucherParametria
    template_name = "vat/voucher/parametria_list.html"
    context_object_name = "parametrias"
    paginate_by = 20

    def get_queryset(self):
        return VoucherParametria.objects.select_related("programa", "creado_por").order_by("-fecha_creacion")


class VoucherParametriaCreateView(LoginRequiredMixin, CreateView):
    model = VoucherParametria
    form_class = VoucherParametriaForm
    template_name = "vat/voucher/parametria_form.html"

    def form_valid(self, form):
        parametria = form.save(commit=False)
        parametria.creado_por = self.request.user
        parametria.save()
        messages.success(self.request, f"Parametría '{parametria.nombre}' creada correctamente.")
        return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": parametria.pk}))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva parametría de voucher"
        return ctx


class VoucherParametriaDetailView(LoginRequiredMixin, DetailView):
    model = VoucherParametria
    template_name = "vat/voucher/parametria_detail.html"
    context_object_name = "parametria"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        parametria = self.object
        qs = parametria.vouchers.select_related("ciudadano", "programa")
        ctx["vouchers"] = qs.order_by("-fecha_asignacion")
        ctx["total"] = qs.count()
        ctx["activos"] = qs.filter(estado="activo").count()
        ctx["agotados"] = qs.filter(estado="agotado").count()
        ctx["vencidos"] = qs.filter(estado="vencido").count()
        ctx["cancelados"] = qs.filter(estado="cancelado").count()
        agg = qs.aggregate(
            total_emitidos=Sum("cantidad_inicial"),
            total_usados=Sum("cantidad_usada"),
            total_disponibles=Sum("cantidad_disponible"),
        )
        ctx["creditos_emitidos"] = agg["total_emitidos"] or 0
        ctx["creditos_usados"] = agg["total_usados"] or 0
        ctx["creditos_disponibles"] = agg["total_disponibles"] or 0
        ctx["pct_uso"] = (
            round(ctx["creditos_usados"] / ctx["creditos_emitidos"] * 100)
            if ctx["creditos_emitidos"] else 0
        )
        ctx["pct_activos"] = (
            round(ctx["activos"] / ctx["total"] * 100)
            if ctx["total"] else 0
        )
        ctx["ultimas"] = qs.order_by("-fecha_asignacion")[:5]
        return ctx


class VoucherParametriaAsignarView(LoginRequiredMixin, View):
    """Asignación individual desde el detail de una parametría."""

    def post(self, request, pk):
        parametria = get_object_or_404(VoucherParametria, pk=pk)
        dni = request.POST.get("dni", "").strip()

        if not dni:
            messages.error(request, "Ingresá un DNI.")
            return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))

        try:
            ciudadano = Ciudadano.objects.get(documento=dni)
        except Ciudadano.DoesNotExist:
            messages.error(request, f"No se encontró ningún ciudadano con DNI {dni}.")
            return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))

        try:
            resultado = _asignar_desde_parametria(ciudadano, parametria, request.user)
        except Exception as e:
            logger.exception("Error asignando voucher desde parametría")
            messages.error(request, f"Error al asignar: {e}")
            return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))

        nombre = ciudadano.nombre_completo
        if resultado == _CREADO:
            messages.success(request, f"Voucher creado y asignado a {nombre}.")
        elif resultado == _REACTIVADO:
            messages.success(request, f"Voucher anterior de {nombre} reactivado con nuevos créditos.")
        elif resultado == _YA_ACTIVO:
            messages.warning(request, f"{nombre} ya tiene un voucher activo para este programa.")
        else:
            messages.error(request, f"No se pudo asignar el voucher a {nombre}.")

        return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))


class VoucherParametriaAsignarMasivoView(LoginRequiredMixin, View):
    """Asignación masiva por lista de DNIs desde el detail de una parametría."""

    def post(self, request, pk):
        parametria = get_object_or_404(VoucherParametria, pk=pk)
        raw = request.POST.get("dnis", "")
        dnis = [d.strip() for d in re.split(r"[\s,;]+", raw) if d.strip()]

        if not dnis:
            messages.error(request, "No ingresaste ningún DNI.")
            return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))
        if len(dnis) > 500:
            messages.error(request, "Máximo 500 DNIs por operación.")
            return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))

        contadores = {_CREADO: [], _REACTIVADO: [], _YA_ACTIVO: [], _NO_ENCONTRADO: [], _ERROR: []}

        for dni in dnis:
            try:
                ciudadano = Ciudadano.objects.get(documento=dni)
            except Ciudadano.DoesNotExist:
                contadores[_NO_ENCONTRADO].append(dni)
                continue
            try:
                resultado = _asignar_desde_parametria(ciudadano, parametria, request.user)
                contadores[resultado].append(dni)
            except Exception:
                logger.exception(f"Error procesando DNI {dni} en asignación masiva")
                contadores[_ERROR].append(dni)

        partes = []
        if contadores[_CREADO]:
            partes.append(f"{len(contadores[_CREADO])} creados")
        if contadores[_REACTIVADO]:
            partes.append(f"{len(contadores[_REACTIVADO])} reactivados")
        if contadores[_YA_ACTIVO]:
            partes.append(f"{len(contadores[_YA_ACTIVO])} ya activos")
        if contadores[_NO_ENCONTRADO]:
            partes.append(f"{len(contadores[_NO_ENCONTRADO])} DNIs no encontrados")
        if contadores[_ERROR]:
            partes.append(f"{len(contadores[_ERROR])} errores")

        exitosos = contadores[_CREADO] + contadores[_REACTIVADO]
        if exitosos:
            messages.success(request, "Asignación masiva completada: " + ", ".join(partes) + ".")
        else:
            messages.warning(request, "No se procesó ningún voucher: " + ", ".join(partes) + ".")

        return redirect(reverse("vat_voucher_parametria_detail", kwargs={"pk": pk}))
