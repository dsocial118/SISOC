from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin


class BusquedaMenu(LoginRequiredMixin, FormView):
    def get(self, request, *args, **kwargs):
        menu = self.request.GET.get("punto_menu")
        puntos = [
            "dashboard",
            "secretarías",
            "secretarias",
            "subsecretarías",
            "subsecretarias",
            "programas",
            "organismos",
            "planes sociales",
            "agentes externos",
            "grupos de destinatarios",
            "tipos de alertas",
            "equipos",
            "acciones",
            "criterios",
            "índices",
            "indices",
            "usuarios",
            "grupos de usuario",
            "legajos",
            "derivaciones",
            "admisiones",
            "intervenciones",
        ]
        if menu and (menu.lower() in puntos):
            menu = menu.lower()
            if menu == "dashboard":
                return redirect("dashboard_listar")
            elif menu == "secretarías" or menu == "secretarias":
                return redirect("secretarias_listar")
            elif menu == "subsecretarías" or menu == "subsecretarias":
                return redirect("subsecretarias_listar")
            elif menu == "programas":
                return redirect("programas_listar")
            elif menu == "organismos":
                return redirect("organismos_listar")
            elif menu == "equipos":
                return redirect("equipos_listar")
            elif menu == "acciones":
                return redirect("acciones_listar")
            elif menu == "criterios":
                return redirect("criterios_listar")
            elif menu == "índices" or menu == "indices":
                return redirect("índices_listar")
            elif menu == "usuarios":
                return redirect("usuarios_listar")
            elif menu == "legajos":
                return redirect("legajos_listar")
            elif menu == "derivaciones":
                return redirect("legajosderivaciones_listar")
            elif menu == "admisiones":
                return redirect("preadmisiones_listar")
            elif menu == "intervenciones":
                return redirect("intervenciones_legajolistar")
            elif menu == "planes sociales":
                return redirect("planes_sociales_listar")
            elif menu == "agentes externos":
                return redirect("agentesexternos_listar")
            elif menu == "grupos de usuario":
                return redirect("grupos_listar")
            elif menu == "grupos de destinatarios":
                return redirect("gruposdestinatarios_listar")
            elif menu == "categorias de alertas":
                return redirect("categoriaalertas_listar")
            elif menu == "alertas":
                return redirect("alertas_listar")
        else:
            messages.error(self.request, ("No existen resultados."))
            return redirect("legajos_listar")
