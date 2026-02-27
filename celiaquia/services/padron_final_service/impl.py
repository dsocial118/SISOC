"""
Servicio para generar padrón final del expediente de celiaquía.
"""

from io import BytesIO
import pandas as pd
from django.db.models import Q
from celiaquia.models import ExpedienteCiudadano, EstadoLegajo


class PadronFinalService:
    """Genera padrón final en Excel para expediente de celiaquía."""

    @staticmethod
    def generar_padron_final_excel(expediente) -> bytes:
        """
        Genera Excel con registros finales del expediente.

        Args:
            expediente: Expediente object

        Returns:
            bytes: Contenido del archivo Excel
        """
        # Obtener legajos válidos (excluir erróneos)
        legajos = (
            ExpedienteCiudadano.objects.filter(expediente=expediente)
            .select_related("ciudadano", "estado")
            .exclude(
                estado__nombre__in=["DOCUMENTO_PENDIENTE", "RECHAZADO", "EXCLUIDO"]
            )
        )

        registros = []

        for legajo in legajos:
            ciudadano = legajo.ciudadano

            # Determinar tipo de registro
            if legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE:
                tipo_registro = "DobleRol"
            elif legajo.rol == ExpedienteCiudadano.ROLE_RESPONSABLE:
                tipo_registro = "Responsable"
            else:
                tipo_registro = "Beneficiario"

            # Datos base
            registro = {
                "TipoRegistro": tipo_registro,
                "Apellido": ciudadano.apellido or "",
                "Nombre": ciudadano.nombre or "",
                "Documento": ciudadano.documento or "",
                "CUIL_CUIT": ciudadano.documento or "",
                "FechaNacimiento": (
                    ciudadano.fecha_nacimiento.strftime("%d/%m/%Y")
                    if ciudadano.fecha_nacimiento
                    else ""
                ),
                "Sexo": ciudadano.sexo.sexo if ciudadano.sexo else "",
                "Provincia": ciudadano.provincia.nombre if ciudadano.provincia else "",
                "Municipio": ciudadano.municipio.nombre if ciudadano.municipio else "",
                "Localidad": ciudadano.localidad.nombre if ciudadano.localidad else "",
                "ExpedienteID": expediente.id,
                "EstadoLegajo": legajo.estado.nombre if legajo.estado else "",
                "RolLegajo": legajo.get_rol_display(),
                "ResponsableDocumento": "",
                "ResponsableNombre": "",
            }

            # Si es beneficiario, buscar responsable
            if tipo_registro == "Beneficiario":
                responsable_legajo = PadronFinalService._obtener_responsable(legajo)
                if responsable_legajo:
                    resp_ciudadano = responsable_legajo.ciudadano
                    registro["ResponsableDocumento"] = resp_ciudadano.documento or ""
                    registro["ResponsableNombre"] = (
                        f"{resp_ciudadano.apellido} {resp_ciudadano.nombre}".strip()
                    )

            registros.append(registro)

        # Crear DataFrame
        df = pd.DataFrame(registros)

        # Orden de columnas
        columnas = [
            "TipoRegistro",
            "Apellido",
            "Nombre",
            "Documento",
            "CUIL_CUIT",
            "FechaNacimiento",
            "Sexo",
            "Provincia",
            "Municipio",
            "Localidad",
            "ExpedienteID",
            "EstadoLegajo",
            "RolLegajo",
            "ResponsableDocumento",
            "ResponsableNombre",
        ]
        df = df[columnas]

        # Generar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="padron_final", index=False)

        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _obtener_responsable(legajo_beneficiario):
        """Obtiene el responsable de un beneficiario si existe."""
        from ciudadanos.models import GrupoFamiliar

        try:
            relacion = GrupoFamiliar.objects.filter(
                ciudadano_2=legajo_beneficiario.ciudadano,
                vinculo=GrupoFamiliar.RELACION_PADRE,
            ).first()

            if relacion:
                return ExpedienteCiudadano.objects.filter(
                    expediente=legajo_beneficiario.expediente,
                    ciudadano=relacion.ciudadano_1,
                    rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
                ).first()
        except Exception:
            pass

        return None
