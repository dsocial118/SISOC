from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from VAT.models import Inscripcion
from VAT.services.reportes_inscripciones_asistencia import (
    build_detalle_personas_inscriptas,
    ReporteFiltros,
    build_reporte_inscripciones_asistencia,
    export_rows_to_csv,
    export_rows_to_excel,
    get_filter_options,
)


class ReporteInscriptosAsistenciasView(LoginRequiredMixin, TemplateView):
    template_name = "vat/reportes/inscripciones_asistencia.html"
    paginate_by = 50

    def _build_filtros(self):
        group_by = self.request.GET.get("group_by", "centro")
        nivel = self.request.GET.get("nivel", "inet")
        return ReporteFiltros(
            nivel=nivel,
            fecha_desde=(self.request.GET.get("fecha_desde") or "").strip(),
            fecha_hasta=(self.request.GET.get("fecha_hasta") or "").strip(),
            provincia_id=(self.request.GET.get("provincia_id") or "").strip(),
            municipio_id=(self.request.GET.get("municipio_id") or "").strip(),
            centro_id=(self.request.GET.get("centro_id") or "").strip(),
            comision_id=(self.request.GET.get("comision_id") or "").strip(),
            curso_id=(self.request.GET.get("curso_id") or "").strip(),
            programa_id=(self.request.GET.get("programa_id") or "").strip(),
            titulo_id=(self.request.GET.get("titulo_id") or "").strip(),
            modalidad_id=(self.request.GET.get("modalidad_id") or "").strip(),
            estado=(self.request.GET.get("estado") or "").strip(),
            usa_voucher=(self.request.GET.get("usa_voucher") or "").strip(),
            estado_curso=(self.request.GET.get("estado_curso") or "").strip(),
            estado_comision=(self.request.GET.get("estado_comision") or "").strip(),
            group_by=group_by,
        )

    def _estado_choices(self):
        return list(Inscripcion.ESTADO_INSCRIPCION_CHOICES)

    def get(self, request, *args, **kwargs):
        filtros = self._build_filtros()
        reporte = build_reporte_inscripciones_asistencia(request.user, filtros)

        export = (request.GET.get("export") or "").lower()
        if export == "csv":
            return export_rows_to_csv(reporte["rows"], reporte["group_by"])
        if export in {"xlsx", "excel"}:
            return export_rows_to_excel(reporte["rows"])

        return self.render_to_response(
            self.get_context_data(reporte=reporte, filtros=filtros)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reporte = kwargs["reporte"]
        filtros = kwargs["filtros"]

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        query_params.pop("export", None)
        querystring = query_params.urlencode()

        paginator = Paginator(reporte["rows"], self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page") or 1)
        detalle_rows = build_detalle_personas_inscriptas(self.request.user, filtros)

        context.update(
            {
                "rows": page_obj.object_list,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "resumen": reporte["resumen"],
                "nivel": reporte["nivel"],
                "nivel_choices": [
                    ("centro", "Centro"),
                    ("provincia", "Provincia"),
                    ("inet", "INET (Global)"),
                ],
                "group_by": reporte["group_by"],
                "group_by_choices": [
                    ("centro", "Centro"),
                    ("provincia", "Provincia"),
                    ("curso", "Curso/Oferta"),
                    ("comision", "Comisión"),
                    ("mes", "Mes de inscripción"),
                ],
                "filtros": filtros,
                "estado_choices": self._estado_choices(),
                "usa_voucher_choices": [
                    ("", "Todos"),
                    ("true", "Sí"),
                    ("false", "No"),
                ],
                "querystring": querystring,
                "detalle_rows": detalle_rows,
                **get_filter_options(self.request.user),
            }
        )
        return context