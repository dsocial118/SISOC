from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from VAT.services.access_scope import is_vat_admin_visualizador, is_vat_sse
from VAT.services.buscador_ciudadano_service import (
    build_resumen,
    build_trayectoria_queryset,
    buscar_ciudadanos,
    contar_inscripciones_visibles,
    export_trayectoria_to_csv,
    export_trayectoria_to_excel,
)

ESTADO_INICIAL = "inicial"
ESTADO_NO_ENCONTRADO = "no_encontrado"
ESTADO_CANDIDATOS = "candidatos"
ESTADO_RESULTADO = "resultado"


class BuscadorCiudadanoView(LoginRequiredMixin, TemplateView):
    template_name = "vat/buscador/ciudadano.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["Pragma"] = "no-cache"
        return response

    def get(self, request, *args, **kwargs):
        context = self._build_context(request, "")
        return self.render_to_response(self.get_context_data(**context))

    def post(self, request, *args, **kwargs):
        q = (request.POST.get("q") or "").strip()
        context = self._build_context(request, q)

        export = (request.POST.get("export") or "").lower()
        ciudadano = context.get("ciudadano")
        if ciudadano and export == "csv":
            return export_trayectoria_to_csv(
                request.user,
                ciudadano,
                inscripciones=context["inscripciones"],
            )
        if ciudadano and export in {"xlsx", "excel"}:
            return export_trayectoria_to_excel(
                request.user,
                ciudadano,
                inscripciones=context["inscripciones"],
            )

        return self.render_to_response(self.get_context_data(**context))

    def _build_context(self, request, q):
        context = {
            "q": q,
            "estado": ESTADO_INICIAL,
            "ciudadano": None,
            "candidatos": [],
            "inscripciones": [],
            "resumen": None,
            "scope_is_national": is_vat_sse(request.user)
            or is_vat_admin_visualizador(request.user),
        }
        if not q:
            return context

        candidatos = list(buscar_ciudadanos(request.user, q))
        if not candidatos:
            context["estado"] = ESTADO_NO_ENCONTRADO
            return context

        if len(candidatos) > 1:
            ciudadano_id = request.POST.get("ciudadano_id") or ""
            if ciudadano_id.isdigit():
                seleccionado = next(
                    (c for c in candidatos if str(c.pk) == ciudadano_id), None
                )
                if seleccionado is not None:
                    candidatos = [seleccionado]

        if len(candidatos) > 1:
            totales = contar_inscripciones_visibles(request.user, candidatos)
            context["estado"] = ESTADO_CANDIDATOS
            context["candidatos"] = [
                {
                    "ciudadano": candidato,
                    "total_inscripciones": totales.get(candidato.pk, 0),
                }
                for candidato in candidatos
            ]
            return context

        ciudadano = candidatos[0]
        inscripciones = list(build_trayectoria_queryset(request.user, ciudadano))
        context.update(
            {
                "estado": ESTADO_RESULTADO,
                "ciudadano": ciudadano,
                "inscripciones": inscripciones,
                "resumen": build_resumen(inscripciones),
            }
        )
        return context
