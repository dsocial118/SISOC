from math import ceil

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from VAT.models import Inscripcion
from VAT.services.reportes_inscripciones_asistencia import (
    DETALLE_PER_PAGE,
    ReporteFiltros,
    build_detalle_queryset,
    build_reporte_inscripciones_asistencia,
    export_detalle_to_csv,
    export_detalle_to_excel,
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
        if export in {"detalle_csv", "detalle-csv"}:
            return export_detalle_to_csv(request.user, filtros)
        if export in {"detalle_xlsx", "detalle_excel", "detalle-xlsx"}:
            return export_detalle_to_excel(request.user, filtros)

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

        # Querystring para el paginador del detalle: conserva la página del
        # resumen (`page`) pero descarta `detalle_page`/`export`.
        detalle_query_params = self.request.GET.copy()
        detalle_query_params.pop("detalle_page", None)
        detalle_query_params.pop("export", None)
        querystring_detalle = detalle_query_params.urlencode()

        paginator = Paginator(reporte["rows"], self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page") or 1)

        # Detalle nominal paginado en el servidor (LIMIT/OFFSET): solo trae la
        # página visible en lugar de un volcado completo. El total se reutiliza
        # del resumen ya calculado para evitar un COUNT extra.
        detalle_qs = build_detalle_queryset(self.request.user, filtros)
        total_detalle = reporte["resumen"].get("inscripciones_total") or 0
        detalle_num_pages = max(1, ceil(total_detalle / DETALLE_PER_PAGE))
        try:
            detalle_page = int(self.request.GET.get("detalle_page") or 1)
        except (TypeError, ValueError):
            detalle_page = 1
        detalle_page = max(1, min(detalle_page, detalle_num_pages))
        detalle_offset = (detalle_page - 1) * DETALLE_PER_PAGE
        detalle_rows = list(
            detalle_qs[detalle_offset : detalle_offset + DETALLE_PER_PAGE]
        )
        detalle_page_info = {
            "number": detalle_page,
            "num_pages": detalle_num_pages,
            "count": total_detalle,
            "per_page": DETALLE_PER_PAGE,
            "has_previous": detalle_page > 1,
            "has_next": detalle_page < detalle_num_pages,
            "previous_page_number": detalle_page - 1,
            "next_page_number": detalle_page + 1,
            "start_index": detalle_offset + 1 if total_detalle else 0,
            "end_index": min(detalle_offset + DETALLE_PER_PAGE, total_detalle),
        }

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
                "querystring_detalle": querystring_detalle,
                "detalle_rows": detalle_rows,
                "detalle_page_info": detalle_page_info,
                **get_filter_options(self.request.user),
            }
        )
        return context
