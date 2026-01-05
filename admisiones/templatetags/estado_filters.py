from django import template

register = template.Library()


@register.filter
def format_estado(value):
    """Convierte códigos de estado a nombres legibles"""
    if not value:
        return value

    # Mapeo de códigos a nombres legibles
    estados_map = {
        # Estados de admisión
        "iniciada": "Iniciada",
        "convenio_seleccionado": "Convenio seleccionado",
        "documentacion_en_proceso": "Documentación en proceso",
        "documentacion_finalizada": "Documentación cargada",
        "documentacion_aprobada": "Documentación aprobada",
        "expediente_cargado": "Expediente cargado",
        "informe_tecnico_en_proceso": "Informe técnico en proceso",
        "informe_tecnico_en_revision": "Informe técnico en revisión",
        "informe_tecnico_en_subsanacion": "Informe técnico en subsanación",
        "informe_tecnico_aprobado": "Informe técnico aprobado",
        "if_informe_tecnico_cargado": "IF Informe técnico cargado",
        "enviado_a_legales": "Enviado a legales",
        "enviado_a_acompaniamiento": "Enviado a acompañamiento",
        "inactivada": "Inactivada",
        "descartado": "Descartado",
        # Estados legales
        "Enviado a Legales": "Enviado a Legales",
        "A Rectificar": "A Rectificar",
        "Rectificado": "Rectificado",
        "Pendiente de Validacion": "Pendiente de Validación",
        "Expediente Agregado": "Expediente Agregado",
        "Formulario Convenio Creado": "Formulario Convenio Creado",
        "IF Convenio Asignado": "IF Convenio Asignado",
        "Formulario Disposición Creado": "Formulario Disposición Creado",
        "IF Disposición Asignado": "IF Disposición Asignado",
        "Juridicos: Validado": "Jurídicos: Validado",
        "Juridicos: Rechazado": "Jurídicos: Rechazado",
        "Disposición Firmada": "Disposición Firmada",
        "Informe SGA Generado": "Informe SGA Generado",
        "Convenio Firmado": "Convenio Firmado",
        "Acompañamiento Pendiente": "Acompañamiento Pendiente",
        "Archivado": "Archivado",
        "Informe Complementario Solicitado": "Informe Complementario Solicitado",
        "Informe Complementario Enviado": "Informe Complementario Enviado",
        "Informe Complementario: Validado": "Informe Complementario: Validado",
        "Finalizado": "Finalizado",
        "Descartado": "Descartado",
        "Inactivada": "Inactivada",
    }

    return estados_map.get(value, value)
