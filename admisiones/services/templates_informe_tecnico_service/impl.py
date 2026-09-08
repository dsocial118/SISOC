import re

from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from admisiones.models.admisiones import (
    IncidenciaTemplateInformeTecnico,
    IncidenciaTemplateInformeTecnicoCaso,
    PlantillaInformeTecnico,
    PlantillaInformeTecnicoPublicacion,
    PlantillaInformeTecnicoVersion,
    VariableTemplateInformeTecnico,
)


class PlantillaInformeTecnicoService:
    """Opera sobre el ciclo de vida del núcleo de templates.

    Conserva la unicidad de publicación y resuelve la versión aplicable a cada
    admisión para que el Informe Técnico pueda generar su DOCX dinámicamente.
    """

    MENSAJE_SIN_PUBLICACION = "No existe una versión publicada de template para la combinación de esta admisión."
    PATRON_VARIABLE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*}}")

    @classmethod
    def validar_variables_publicables(cls, contenido_html):
        """Valida que el borrador publicado use sólo variables activas.

        Se permiten borradores incompletos para no perder trabajo. La validación
        se aplica al publicar, que es el momento en que el contenido pasa a ser
        operativo para los Informes Técnicos.
        """

        expresiones = set(cls.PATRON_VARIABLE.findall(contenido_html or ""))
        if not expresiones:
            return True, ""

        variables_activas = set(
            VariableTemplateInformeTecnico.objects.filter(activo=True).values_list(
                "codigo", flat=True
            )
        )
        no_catalogadas = sorted(expresiones - variables_activas)
        if not no_catalogadas:
            return True, ""

        listado = ", ".join(f"{{{{ {codigo} }}}}" for codigo in no_catalogadas)
        return (
            False,
            "El contenido usa variables que no están activas en el catálogo: "
            f"{listado}. Actívelas o reemplácelas antes de publicar.",
        )

    @staticmethod
    def resolver_publicacion_para_admision(admision):
        """Devuelve la versión publicada aplicable a una admisión.

        La consulta usa el índice de publicación, que garantiza una sola versión
        vigente para cada combinación. No hay template por defecto.
        """

        if not getattr(admision, "tipo", None):
            return None, "La admisión no tiene tipo de trámite definido."
        if not getattr(admision, "tipo_convenio_id", None):
            return None, "La admisión no tiene tipo de convenio definido."

        if admision.tipo == "incorporacion":
            if not getattr(admision, "es_ex_pnud", None):
                return None, "Falta completar si la admisión es Ex PNUD."
            if admision.es_ex_pnud == "si" and not getattr(
                admision, "estado_convenio_pnud", None
            ):
                return None, "Falta completar el estado del convenio PNUD."
        elif admision.tipo == "renovacion":
            if not getattr(admision, "tipo_renovacion", None):
                return None, "Falta completar el tipo de renovación."
            if not getattr(admision, "estado_financiamiento", None):
                return None, "Falta completar el estado del financiamiento."
            if not getattr(
                admision, "informe_complementario_modifica_prestaciones", None
            ):
                return None, (
                    "Falta indicar si se realizó un Informe Complementario para modificar prestaciones."
                )
        else:
            return None, "El tipo de trámite de la admisión no es válido."

        clave_condiciones = PlantillaInformeTecnico.construir_clave_condiciones(
            tipo_admision=admision.tipo,
            tipo_convenio_id=admision.tipo_convenio_id,
            es_ex_pnud=getattr(admision, "es_ex_pnud", None),
            estado_convenio_pnud=getattr(admision, "estado_convenio_pnud", None),
            tipo_renovacion=getattr(admision, "tipo_renovacion", None),
            estado_financiamiento=getattr(admision, "estado_financiamiento", None),
            informe_complementario_modifica_prestaciones=getattr(
                admision, "informe_complementario_modifica_prestaciones", None
            ),
        )
        publicacion = (
            PlantillaInformeTecnicoPublicacion.objects.select_related(
                "plantilla",
                "version",
            )
            .filter(
                clave_condiciones=clave_condiciones,
                plantilla__estado="activa",
                version__estado="publicada",
            )
            .first()
        )
        if publicacion is None:
            return None, PlantillaInformeTecnicoService.MENSAJE_SIN_PUBLICACION
        return publicacion, None

    @staticmethod
    def es_configuracion_faltante(error_template):
        return error_template == PlantillaInformeTecnicoService.MENSAJE_SIN_PUBLICACION

    @staticmethod
    def detalle_configuracion_faltante(admision, error_template=None):
        """Construye datos serializables y copiados para una incidencia."""

        tipo_convenio = getattr(admision, "tipo_convenio", None)
        condiciones = {
            "tipo_admision": {
                "valor": getattr(admision, "tipo", None),
                "descripcion": getattr(
                    admision,
                    "get_tipo_display",
                    lambda: getattr(admision, "tipo", ""),
                )(),
            },
            "tipo_convenio": {
                "id": getattr(admision, "tipo_convenio_id", None),
                "descripcion": getattr(tipo_convenio, "nombre", ""),
            },
        }
        if getattr(admision, "tipo", None) == "incorporacion":
            condiciones.update(
                {
                    "es_ex_pnud": {
                        "valor": getattr(admision, "es_ex_pnud", None),
                        "descripcion": getattr(
                            admision,
                            "get_es_ex_pnud_display",
                            lambda: getattr(admision, "es_ex_pnud", ""),
                        )(),
                    },
                    "estado_convenio_pnud": {
                        "valor": getattr(admision, "estado_convenio_pnud", None),
                        "descripcion": getattr(
                            admision,
                            "get_estado_convenio_pnud_display",
                            lambda: getattr(
                                admision,
                                "estado_convenio_pnud",
                                "",
                            ),
                        )(),
                    },
                }
            )
        elif getattr(admision, "tipo", None) == "renovacion":
            condiciones.update(
                {
                    "tipo_renovacion": {
                        "valor": getattr(admision, "tipo_renovacion", None),
                        "descripcion": getattr(
                            admision,
                            "get_tipo_renovacion_display",
                            lambda: getattr(admision, "tipo_renovacion", ""),
                        )(),
                    },
                    "estado_financiamiento": {
                        "valor": getattr(admision, "estado_financiamiento", None),
                        "descripcion": getattr(
                            admision,
                            "get_estado_financiamiento_display",
                            lambda: getattr(
                                admision,
                                "estado_financiamiento",
                                "",
                            ),
                        )(),
                    },
                    "informe_complementario_modifica_prestaciones": {
                        "valor": getattr(
                            admision,
                            "informe_complementario_modifica_prestaciones",
                            None,
                        ),
                        "descripcion": getattr(
                            admision,
                            "get_informe_complementario_modifica_prestaciones_display",
                            lambda: getattr(
                                admision,
                                "informe_complementario_modifica_prestaciones",
                                "",
                            ),
                        )(),
                    },
                }
            )

        clave_condiciones = PlantillaInformeTecnico.construir_clave_condiciones(
            tipo_admision=getattr(admision, "tipo", None),
            tipo_convenio_id=getattr(admision, "tipo_convenio_id", None),
            es_ex_pnud=getattr(admision, "es_ex_pnud", None),
            estado_convenio_pnud=getattr(admision, "estado_convenio_pnud", None),
            tipo_renovacion=getattr(admision, "tipo_renovacion", None),
            estado_financiamiento=getattr(admision, "estado_financiamiento", None),
            informe_complementario_modifica_prestaciones=getattr(
                admision, "informe_complementario_modifica_prestaciones", None
            ),
        )
        return {
            "clave_condiciones": clave_condiciones,
            "condiciones": condiciones,
            "mensaje_funcional": error_template or "",
        }

    @staticmethod
    def _obtener_o_crear_incidencia_abierta(clave_condiciones, condiciones, usuario):
        incidencia = (
            IncidenciaTemplateInformeTecnico.objects.select_for_update()
            .filter(clave_abierta=clave_condiciones)
            .first()
        )
        if incidencia is not None:
            return incidencia

        incidencia_anterior = (
            IncidenciaTemplateInformeTecnico.objects.filter(
                clave_condiciones=clave_condiciones,
                clave_abierta__isnull=True,
            )
            .order_by("-ultima_fecha")
            .first()
        )
        try:
            with transaction.atomic():
                return IncidenciaTemplateInformeTecnico.objects.create(
                    clave_condiciones=clave_condiciones,
                    clave_abierta=clave_condiciones,
                    condiciones=condiciones,
                    incidencia_anterior=incidencia_anterior,
                    creado_por=usuario,
                    modificado_por=usuario,
                )
        except IntegrityError:
            return IncidenciaTemplateInformeTecnico.objects.select_for_update().get(
                clave_abierta=clave_condiciones
            )

    @staticmethod
    def _registrar_caso_incidencia(incidencia, admision, informe, usuario, detalle):
        informe_pk = getattr(informe, "pk", None)
        comedor = getattr(admision, "comedor", None)
        organizacion = getattr(comedor, "organizacion", None)
        programa = getattr(comedor, "programa", None)
        _, creado = IncidenciaTemplateInformeTecnicoCaso.objects.get_or_create(
            incidencia=incidencia,
            referencia_caso=f"admision:{admision.pk}|informe:{informe_pk or '-'}",
            defaults={
                "admision": admision,
                "admision_id_reportada": admision.pk,
                "informe": informe,
                "informe_id_reportado": informe_pk,
                "comedor_nombre": getattr(comedor, "nombre", "") or "",
                "organizacion_nombre": getattr(organizacion, "nombre", "") or "",
                "programa_nombre": getattr(programa, "nombre", "") or "",
                "estado_admision": getattr(admision, "estado_admision", "") or "",
                "detalle": detalle,
                "reportado_por": usuario,
            },
        )
        return creado

    @staticmethod
    @transaction.atomic
    def reportar_configuracion_faltante(admision, informe, usuario):
        """Crea o agrupa un reporte solo para una combinación sin publicación."""

        publicacion, error_template = (
            PlantillaInformeTecnicoService.resolver_publicacion_para_admision(admision)
        )
        if publicacion is not None:
            return None, "Ya existe una versión publicada para esta admisión."
        if not PlantillaInformeTecnicoService.es_configuracion_faltante(error_template):
            return None, error_template
        if informe is not None and getattr(informe, "admision_id", None) != admision.pk:
            return None, "El Informe Técnico no corresponde a la admisión indicada."

        detalle = PlantillaInformeTecnicoService.detalle_configuracion_faltante(
            admision,
            error_template,
        )
        incidencia = PlantillaInformeTecnicoService._obtener_o_crear_incidencia_abierta(
            detalle["clave_condiciones"],
            detalle["condiciones"],
            usuario,
        )
        creado = PlantillaInformeTecnicoService._registrar_caso_incidencia(
            incidencia,
            admision,
            informe,
            usuario,
            detalle,
        )
        incidencia.cantidad_casos = incidencia.casos.count()
        incidencia.modificado_por = usuario
        incidencia.save(
            update_fields=["cantidad_casos", "modificado_por", "ultima_fecha"]
        )
        mensaje = (
            "La configuración pendiente fue registrada para que los referentes del sistema puedan revisarla."
            if creado
            else "Esta admisión ya estaba registrada en una configuración pendiente."
        )
        return incidencia, mensaje

    @staticmethod
    @transaction.atomic
    def gestionar_incidencia(incidencia, datos, usuario):
        """Actualiza el estado del buzón preservando una sola incidencia abierta."""

        incidencia = IncidenciaTemplateInformeTecnico.objects.select_for_update().get(
            pk=incidencia.pk
        )
        nuevo_estado = datos["estado"]
        if nuevo_estado in IncidenciaTemplateInformeTecnico.ESTADOS_ABIERTOS:
            otra_abierta = (
                IncidenciaTemplateInformeTecnico.objects.select_for_update()
                .filter(clave_abierta=incidencia.clave_condiciones)
                .exclude(pk=incidencia.pk)
                .first()
            )
            if otra_abierta:
                return (
                    False,
                    f"La incidencia {otra_abierta.codigo} ya está abierta para esta combinación.",
                )
            incidencia.clave_abierta = incidencia.clave_condiciones
        else:
            incidencia.clave_abierta = None

        incidencia.estado = nuevo_estado
        incidencia.observaciones = datos.get("observaciones", "")
        incidencia.plantilla = datos.get("plantilla")
        incidencia.modificado_por = usuario
        try:
            incidencia.save(
                update_fields=[
                    "clave_abierta",
                    "estado",
                    "observaciones",
                    "plantilla",
                    "modificado_por",
                    "ultima_fecha",
                ]
            )
        except IntegrityError:
            return (
                False,
                "No se pudo reabrir la incidencia porque ya existe otra abierta para esta combinación.",
            )
        return True, "Incidencia actualizada correctamente."

    @staticmethod
    @transaction.atomic
    def crear_plantilla(datos, usuario):
        plantilla = PlantillaInformeTecnico(
            creado_por=usuario,
            modificado_por=usuario,
            **datos,
        )
        plantilla.full_clean()
        plantilla.save()
        version = PlantillaInformeTecnicoVersion.objects.create(
            plantilla=plantilla,
            numero=1,
            creado_por=usuario,
        )
        return plantilla, version

    @staticmethod
    @transaction.atomic
    def crear_version_borrador(plantilla, usuario, origen=None):
        plantilla = PlantillaInformeTecnico.objects.select_for_update().get(
            pk=plantilla.pk
        )
        if plantilla.estado == "eliminada":
            return None, "No se pueden crear versiones de una plantilla eliminada."

        borrador_existente = (
            PlantillaInformeTecnicoVersion.objects.select_for_update()
            .filter(plantilla=plantilla, estado="borrador")
            .order_by("-modificado", "-numero")
            .first()
        )
        if borrador_existente:
            return (
                borrador_existente,
                "Ya existe una versión en preparación. Puede continuar editándola.",
            )

        ultimo_numero = (
            PlantillaInformeTecnicoVersion.objects.filter(
                plantilla=plantilla
            ).aggregate(ultimo=Max("numero"))["ultimo"]
            or 0
        )
        contenido_html = ""
        observaciones = ""
        if origen is not None:
            contenido_html = origen.contenido_html
            observaciones = origen.observaciones
        version = PlantillaInformeTecnicoVersion.objects.create(
            plantilla=plantilla,
            numero=ultimo_numero + 1,
            contenido_html=contenido_html,
            observaciones=observaciones,
            creado_por=usuario,
        )
        return version, "Versión en preparación creada correctamente."

    @staticmethod
    @transaction.atomic
    def descartar_borrador(version, usuario):
        version = (
            PlantillaInformeTecnicoVersion.objects.select_for_update()
            .select_related("plantilla")
            .get(pk=version.pk)
        )
        if version.estado != "borrador":
            return False, "Solo se pueden descartar versiones en preparación."

        plantilla = version.plantilla
        version.delete()
        plantilla.modificado_por = usuario
        plantilla.save(update_fields=["modificado_por", "modificado"])
        return True, "La versión en preparación fue descartada."

    @staticmethod
    @transaction.atomic
    def guardar_borrador(version, datos, usuario):
        version = PlantillaInformeTecnicoVersion.objects.select_for_update().get(
            pk=version.pk
        )
        if version.estado != "borrador":
            return False, "Solo se pueden editar versiones en borrador."

        version.contenido_html = datos["contenido_html"]
        version.observaciones = datos["observaciones"]
        version.save(update_fields=["contenido_html", "observaciones", "modificado"])
        plantilla = version.plantilla
        plantilla.modificado_por = usuario
        plantilla.save(update_fields=["modificado_por", "modificado"])
        return True, "Versión en preparación guardada correctamente."

    @classmethod
    @transaction.atomic
    def publicar_version(cls, version, usuario):
        version = (
            PlantillaInformeTecnicoVersion.objects.select_for_update()
            .select_related("plantilla")
            .get(pk=version.pk)
        )
        plantilla = PlantillaInformeTecnico.objects.select_for_update().get(
            pk=version.plantilla_id
        )
        if plantilla.estado != "activa":
            return False, "Solo se puede publicar una plantilla lógica activa."
        if version.estado == "publicada":
            return True, "La versión ya se encuentra publicada."
        if version.estado != "borrador":
            return False, "Solo se pueden publicar versiones en borrador."
        if not version.contenido_html.strip():
            return False, "Debe ingresar contenido antes de publicar la versión."
        variables_validas, mensaje_variables = cls.validar_variables_publicables(
            version.contenido_html
        )
        if not variables_validas:
            return False, mensaje_variables

        clave_condiciones = plantilla.clave_condiciones
        publicacion_conflictiva = (
            PlantillaInformeTecnicoPublicacion.objects.select_for_update()
            .select_related("plantilla")
            .filter(clave_condiciones=clave_condiciones)
            .exclude(plantilla=plantilla)
            .first()
        )
        if publicacion_conflictiva:
            return (
                False,
                "Ya existe una plantilla publicada para esta combinación: "
                f"{publicacion_conflictiva.plantilla.codigo} - "
                f"{publicacion_conflictiva.plantilla.nombre}.",
            )

        publicacion_actual = (
            PlantillaInformeTecnicoPublicacion.objects.select_for_update()
            .select_related("version")
            .filter(plantilla=plantilla)
            .first()
        )
        if publicacion_actual:
            version_anterior = publicacion_actual.version
            version_anterior.estado = "inactiva"
            version_anterior.save(update_fields=["estado", "modificado"])

        version.estado = "publicada"
        version.publicado = timezone.now()
        version.publicado_por = usuario
        version.save(
            update_fields=["estado", "publicado", "publicado_por", "modificado"]
        )

        try:
            if publicacion_actual:
                publicacion_actual.clave_condiciones = clave_condiciones
                publicacion_actual.version = version
                publicacion_actual.publicada_por = usuario
                publicacion_actual.save(
                    update_fields=[
                        "clave_condiciones",
                        "version",
                        "publicada_por",
                    ]
                )
            else:
                PlantillaInformeTecnicoPublicacion.objects.create(
                    clave_condiciones=clave_condiciones,
                    plantilla=plantilla,
                    version=version,
                    publicada_por=usuario,
                )
        except IntegrityError:
            return (
                False,
                "Otra plantilla fue publicada para esta combinación. Actualice la pantalla e intente nuevamente.",
            )

        return True, "Versión publicada correctamente."

    @staticmethod
    @transaction.atomic
    def inactivar_plantilla(plantilla, usuario):
        plantilla = PlantillaInformeTecnico.objects.select_for_update().get(
            pk=plantilla.pk
        )
        if plantilla.estado != "activa":
            return False, "La plantilla ya no se encuentra activa."

        publicacion = (
            PlantillaInformeTecnicoPublicacion.objects.select_for_update()
            .select_related("version")
            .filter(plantilla=plantilla)
            .first()
        )
        if publicacion:
            publicacion.version.estado = "inactiva"
            publicacion.version.save(update_fields=["estado", "modificado"])
            publicacion.delete()

        plantilla.estado = "inactiva"
        plantilla.modificado_por = usuario
        plantilla.save(update_fields=["estado", "modificado_por", "modificado"])
        return True, "Plantilla inactivada correctamente."
