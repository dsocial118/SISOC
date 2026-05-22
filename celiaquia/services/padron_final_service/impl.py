"""
Servicio para generar padrón final del expediente de celiaquía.

Genera un Excel con la nómina de beneficiarios aprobados (revision_tecnico
APROBADO + resultado_sintys MATCH) respetando la misma estructura de columnas
que la plantilla de importación que carga la provincia.
"""

from io import BytesIO

import pandas as pd

from celiaquia.models import (
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)


COLUMNAS_PADRON = [
    "apellido",
    "nombre",
    "documento",
    "fecha_nacimiento",
    "sexo",
    "nacionalidad",
    "municipio",
    "localidad",
    "calle",
    "altura",
    "codigo_postal",
    "telefono",
    "email",
    "APELLIDO_RESPONSABLE",
    "NOMBRE_REPSONSABLE",
    "Cuit_Responsable",
    "FECHA_DE_NACIMIENTO_RESPONSABLE",
    "SEXO_RESPONSABLE",
    "DOMICILIO_RESPONSABLE",
    "LOCALIDAD_RESPONSABLE",
    "CELULAR_RESPONSABLE",
    "CORREO_RESPONSABLE",
]


def _fmt_fecha(fecha) -> str:
    if not fecha:
        return ""
    try:
        return fecha.strftime("%d/%m/%Y")
    except AttributeError:
        return str(fecha)


def _domicilio(ciudadano) -> str:
    if ciudadano is None:
        return ""
    calle = (ciudadano.calle or "").strip()
    altura = (ciudadano.altura or "").strip() if ciudadano.altura else ""
    if calle and altura:
        return f"{calle} {altura}"
    return calle or altura or ""


class PadronFinalService:
    """Genera padrón final en Excel para expediente de celiaquía."""

    @staticmethod
    def generar_padron_final_excel(expediente) -> bytes:
        """Genera Excel con los beneficiarios aprobados del expediente.

        Filtra los legajos con ``revision_tecnico=APROBADO`` y
        ``resultado_sintys=MATCH`` y emite una fila por beneficiario
        (incluye ``ROLE_BENEFICIARIO`` y ``ROLE_BENEFICIARIO_Y_RESPONSABLE``).
        Si el beneficiario tiene responsable, sus datos se incluyen en las
        columnas ``*_RESPONSABLE``.
        """
        from celiaquia.services.familia_service import FamiliaService

        legajos = (
            ExpedienteCiudadano.objects.filter(
                expediente=expediente,
                revision_tecnico=RevisionTecnico.APROBADO,
                resultado_sintys=ResultadoSintys.MATCH,
                rol__in=[
                    ExpedienteCiudadano.ROLE_BENEFICIARIO,
                    ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE,
                ],
            )
            .select_related(
                "ciudadano",
                "ciudadano__sexo",
                "ciudadano__nacionalidad",
                "ciudadano__municipio",
                "ciudadano__localidad",
            )
            .order_by("ciudadano__apellido", "ciudadano__nombre")
        )

        ciudadanos_ids = list(legajos.values_list("ciudadano_id", flat=True))
        responsables_por_hijo = FamiliaService.obtener_responsables_por_hijo(
            ciudadanos_ids
        )

        registros = []
        for legajo in legajos:
            ciudadano = legajo.ciudadano
            registro = {
                "apellido": ciudadano.apellido or "",
                "nombre": ciudadano.nombre or "",
                "documento": ciudadano.documento or "",
                "fecha_nacimiento": _fmt_fecha(ciudadano.fecha_nacimiento),
                "sexo": ciudadano.sexo.sexo if ciudadano.sexo else "",
                "nacionalidad": (
                    ciudadano.nacionalidad.nombre if ciudadano.nacionalidad else ""
                ),
                "municipio": ciudadano.municipio.nombre if ciudadano.municipio else "",
                "localidad": ciudadano.localidad.nombre if ciudadano.localidad else "",
                "calle": ciudadano.calle or "",
                "altura": ciudadano.altura or "",
                "codigo_postal": ciudadano.codigo_postal or "",
                "telefono": ciudadano.telefono or "",
                "email": ciudadano.email or "",
                "APELLIDO_RESPONSABLE": "",
                "NOMBRE_REPSONSABLE": "",
                "Cuit_Responsable": "",
                "FECHA_DE_NACIMIENTO_RESPONSABLE": "",
                "SEXO_RESPONSABLE": "",
                "DOMICILIO_RESPONSABLE": "",
                "LOCALIDAD_RESPONSABLE": "",
                "CELULAR_RESPONSABLE": "",
                "CORREO_RESPONSABLE": "",
            }

            responsables = responsables_por_hijo.get(ciudadano.id, [])
            if responsables:
                resp = responsables[0]
                registro["APELLIDO_RESPONSABLE"] = resp.apellido or ""
                registro["NOMBRE_REPSONSABLE"] = resp.nombre or ""
                registro["Cuit_Responsable"] = resp.cuil_cuit or (resp.documento or "")
                registro["FECHA_DE_NACIMIENTO_RESPONSABLE"] = _fmt_fecha(
                    resp.fecha_nacimiento
                )
                registro["SEXO_RESPONSABLE"] = resp.sexo.sexo if resp.sexo else ""
                registro["DOMICILIO_RESPONSABLE"] = _domicilio(resp)
                registro["LOCALIDAD_RESPONSABLE"] = (
                    resp.localidad.nombre if resp.localidad else ""
                )
                registro["CELULAR_RESPONSABLE"] = resp.telefono or ""
                registro["CORREO_RESPONSABLE"] = resp.email or ""

            registros.append(registro)

        df = pd.DataFrame(registros, columns=COLUMNAS_PADRON)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="padron_final", index=False)

        output.seek(0)
        return output.getvalue()
