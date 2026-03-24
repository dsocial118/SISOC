import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, View
from django.views import View
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db.models import Q

from ciudadanos.models import Ciudadano
from VAT.models import Voucher, VoucherRecarga
from VAT.forms import VoucherForm, VoucherRecargaForm, VoucherAsignacionMasivaForm
from VAT.services.voucher_service.impl import VoucherService

logger = logging.getLogger("django")


class VoucherListView(LoginRequiredMixin, ListView):
    model = Voucher
    template_name = "vat/voucher/voucher_list.html"
    context_object_name = "vouchers"
    paginate_by = 20

    def get_queryset(self):
        qs = Voucher.objects.select_related("ciudadano", "programa").order_by("-fecha_asignacion")
        estado = self.request.GET.get("estado")
        programa = self.request.GET.get("programa")
        buscar = self.request.GET.get("q")
        if estado:
            qs = qs.filter(estado=estado)
        if programa:
            qs = qs.filter(programa_id=programa)
        if buscar:
            qs = qs.filter(
                Q(ciudadano__nombre__icontains=buscar)
                | Q(ciudadano__apellido__icontains=buscar)
                | Q(ciudadano__documento__icontains=buscar)
            )
        return qs

    def get_context_data(self, **kwargs):
        from core.models import Programa
        ctx = super().get_context_data(**kwargs)
        ctx["estado_choices"] = Voucher.ESTADO_CHOICES
        ctx["programas"] = Programa.objects.only("id", "nombre")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado_sel"] = self.request.GET.get("estado", "")
        ctx["programa_sel"] = self.request.GET.get("programa", "")
        return ctx


class VoucherDetailView(LoginRequiredMixin, DetailView):
    model = Voucher
    template_name = "vat/voucher/voucher_detail.html"
    context_object_name = "voucher"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        voucher = self.object
        ctx["estado_info"] = VoucherService.obtener_estado_actual(voucher)
        ctx["recargas"] = voucher.recargas.select_related("autorizado_por").order_by("-fecha_recarga")
        ctx["usos"] = voucher.usos.select_related("inscripcion_oferta__oferta").order_by("-fecha_uso")
        ctx["logs"] = voucher.logs.order_by("-fecha_evento")
        ctx["recarga_form"] = VoucherRecargaForm()
        return ctx


class VoucherCreateView(LoginRequiredMixin, CreateView):
    model = Voucher
    form_class = VoucherForm
    template_name = "vat/voucher/voucher_form.html"

    def get_initial(self):
        initial = super().get_initial()
        ciudadano_id = self.request.GET.get("ciudadano")
        if ciudadano_id:
            initial["ciudadano"] = ciudadano_id
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            voucher = VoucherService.crear_voucher(
                ciudadano_id=data["ciudadano"].id,
                programa_id=data["programa"].id,
                cantidad=data["cantidad_inicial"],
                fecha_vencimiento=data["fecha_vencimiento"],
                usuario=self.request.user,
            )
            messages.success(self.request, f"Voucher asignado exitosamente a {data['ciudadano']}.")
            return redirect(reverse("vat_voucher_detail", kwargs={"pk": voucher.pk}))
        except Exception as e:
            logger.exception("Error creando voucher")
            messages.error(self.request, f"Error al crear el voucher: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Asignar Voucher"
        return ctx


class VoucherRecargaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        voucher = get_object_or_404(Voucher, pk=pk)
        form = VoucherRecargaForm(request.POST)
        if form.is_valid():
            ok, msg = VoucherService.recargar_voucher(
                voucher=voucher,
                cantidad=form.cleaned_data["cantidad"],
                motivo=form.cleaned_data["motivo"],
                usuario=request.user,
            )
            if ok:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
        else:
            messages.error(request, "Datos de recarga inválidos.")
        return redirect(reverse("vat_voucher_detail", kwargs={"pk": pk}))


class VoucherCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        voucher = get_object_or_404(Voucher, pk=pk)
        ok = VoucherService.cancelar_voucher(voucher=voucher, usuario=request.user)
        if ok:
            messages.success(request, "Voucher cancelado correctamente.")
        else:
            messages.warning(request, "El voucher ya estaba cancelado.")
        return redirect(reverse("vat_voucher_detail", kwargs={"pk": pk}))


class VoucherAsignacionMasivaView(LoginRequiredMixin, View):
    template_name = "vat/voucher/voucher_asignacion_masiva.html"

    def get(self, request):
        form = VoucherAsignacionMasivaForm()
        return self._render(request, form)

    def post(self, request):
        form = VoucherAsignacionMasivaForm(request.POST)
        if not form.is_valid():
            return self._render(request, form)

        data = form.cleaned_data
        dnis = data["dnis"]
        programa_id = data["programa"].id
        cantidad = data["cantidad_inicial"]
        fecha_vencimiento = data["fecha_vencimiento"]

        creados = []
        no_encontrados = []
        ya_tenia = []
        errores = []

        # Batch: una query para todos los ciudadanos y otra para los que ya tienen voucher activo
        ciudadanos_map = {
            c.documento: c
            for c in Ciudadano.objects.filter(documento__in=dnis)
        }
        con_voucher_activo = set(
            Voucher.objects.filter(
                ciudadano__documento__in=dnis,
                programa_id=programa_id,
                estado="activo",
            ).values_list("ciudadano__documento", flat=True)
        )

        for dni in dnis:
            ciudadano = ciudadanos_map.get(dni)
            if not ciudadano:
                no_encontrados.append(dni)
                continue
            if dni in con_voucher_activo:
                ya_tenia.append(dni)
                continue
            try:
                VoucherService.crear_voucher(
                    ciudadano_id=ciudadano.id,
                    programa_id=programa_id,
                    cantidad=cantidad,
                    fecha_vencimiento=fecha_vencimiento,
                    usuario=request.user,
                )
                creados.append(dni)
            except Exception as e:
                logger.exception(f"Error creando voucher masivo para DNI {dni}: {e}")
                errores.append(dni)

        return self._render(request, form, resultado={
            "creados": creados,
            "no_encontrados": no_encontrados,
            "ya_tenia": ya_tenia,
            "errores": errores,
        })

    def _render(self, request, form, resultado=None):
        from django.shortcuts import render
        return render(request, self.template_name, {
            "form": form,
            "resultado": resultado,
        })
