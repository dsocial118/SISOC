from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView


class BusquedaMenu(LoginRequiredMixin, FormView):
    def get(self, request, *args, **kwargs):
        menu = self.request.GET.get("punto_menu")
        menu_mapping = {
            "dashboard": "dashboard_listar",
            "secretarías": "secretarias_listar",
            "secretarias": "secretarias_listar",
            "subsecretarías": "subsecretarias_listar",
            "subsecretarias": "subsecretarias_listar",
            "programas": "programas_listar",
            "organismos": "organismos_listar",
            "equipos": "equipos_listar",
            "acciones": "acciones_listar",
            "criterios": "criterios_listar",
            "índices": "índices_listar",
            "indices": "índices_listar",
            "usuarios": "usuarios_listar",
            "legajos": "legajos_listar",
            "derivaciones": "legajosderivaciones_listar",
            "admisiones": "preadmisiones_listar",
            "intervenciones": "intervenciones_legajolistar",
            "planes sociales": "planes_sociales_listar",
            "agentes externos": "agentesexternos_listar",
            "grupos de usuario": "grupos_listar",
            "grupos de destinatarios": "gruposdestinatarios_listar",
            "categorias de alertas": "categoriaalertas_listar",
            "alertas": "alertas_listar",
        }

        if menu:
            menu = menu.lower()
            if menu in menu_mapping:
                return redirect(menu_mapping[menu])

        messages.error(self.request, "No existen resultados.")
        return redirect("legajos_listar")
