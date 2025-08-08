from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from admisiones.utils import generar_texto_comidas
import logging

logger = logging.getLogger(__name__)

from admisiones.models.admisiones import (
    InformeTecnico,
    CampoASubsanar,
    ObservacionGeneralInforme,
    InformeTecnicoPDF,
    Admision,
    InformeComplementario,
    InformeComplementarioCampos,
    Anexo,
)
from admisiones.forms.admisiones_forms import (
    InformeTecnicoJuridicoForm,
    InformeTecnicoBaseForm,
)


class InformeService:
    @staticmethod
    def get_form_class_por_tipo(tipo):
        try:
            return (
                InformeTecnicoJuridicoForm
                if tipo == "juridico"
                else InformeTecnicoBaseForm
            )
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_form_class_por_tipo", exc_info=True
            )
            return InformeTecnicoBaseForm

    @staticmethod
    def get_tipo_from_kwargs(kwargs):
        try:
            return kwargs.get("tipo", "base")
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_tipo_from_kwargs", exc_info=True
            )
            return "base"

    @staticmethod
    def get_queryset_informe_por_tipo(tipo):
        try:
            return InformeTecnico.objects.filter(tipo=tipo)
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_queryset_informe_por_tipo",
                exc_info=True,
            )
            return InformeTecnico.objects.none()

    @staticmethod
    def get_admision_y_tipo_from_kwargs(kwargs):
        try:
            tipo = kwargs.get("tipo", "base")
            admision_id = kwargs.get("admision_id")
            admision = get_object_or_404(Admision, pk=admision_id)
            return admision, tipo
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_admision_y_tipo_from_kwargs",
                exc_info=True,
            )
            return None, "base"

    @staticmethod
    def verificar_estado_para_revision(informe):
        try:
            if informe.estado != "Validado":
                CampoASubsanar.objects.filter(informe=informe).delete()
                ObservacionGeneralInforme.objects.filter(informe=informe).delete()
                informe.estado = "Para revision"
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en verificar_estado_para_revision",
                exc_info=True,
            )

    @staticmethod
    def get_campos_visibles_informe(informe):
        try:
            campos_excluidos_comunes = ["id", "admision", "estado", "tipo"]

            if informe.tipo == "juridico":
                campos_excluidos_especificos = [
                    "declaracion_jurada_recepcion_subsidios",
                    "constancia_inexistencia_percepcion_otros_subsidios",
                    "organizacion_avalista_1",
                    "organizacion_avalista_2",
                    "material_difusion_vinculado",
                ]
            elif informe.tipo == "base":
                campos_excluidos_especificos = [
                    "validacion_registro_nacional",
                    "IF_relevamiento_territorial",
                ]
            else:
                campos_excluidos_especificos = []

            campos_excluidos = campos_excluidos_comunes + campos_excluidos_especificos

            return [
                (field.verbose_name, getattr(informe, field.name))
                for field in informe._meta.fields
                if field.name not in campos_excluidos
            ]
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_campos_visibles_informe",
                exc_info=True,
            )
            return []

    @staticmethod
    def preparar_informe_para_creacion(instance, admision_id):
        try:
            instance.admision_id = admision_id
            instance.estado = "Para revision"
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en preparar_informe_para_creacion",
                exc_info=True,
            )

    @staticmethod
    def get_informe_por_tipo_y_pk(tipo, pk):
        try:
            return get_object_or_404(InformeTecnico, tipo=tipo, pk=pk)
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_informe_por_tipo_y_pk",
                exc_info=True,
            )
            return None

    @staticmethod
    def actualizar_estado_informe(informe, nuevo_estado, tipo=None):
        try:
            informe.estado = nuevo_estado
            informe.save()

            if nuevo_estado == "Validado":
                InformeService.generar_y_guardar_pdf(informe, tipo)
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en actualizar_estado_informe",
                exc_info=True,
            )

    @staticmethod
    def generar_y_guardar_pdf(informe, tipo):
        try:
            anexo = Anexo.objects.filter(admision=informe.admision).first()
            texto_comidas = generar_texto_comidas(anexo)

            html_string = render_to_string(
                "pdf_informe_tecnico.html",
                {
                    "informe": informe,
                    "anexo": anexo,
                },
            )

            pdf_file = HTML(string=html_string).write_pdf()
            nombre_archivo = f"{tipo}_informe_{informe.id}.pdf"
            pdf_content = ContentFile(pdf_file, name=nombre_archivo)

            InformeTecnicoPDF.objects.create(
                admision=informe.admision,
                tipo=tipo,
                informe_id=informe.id,
                archivo=pdf_content,
            )
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en generar_y_guardar_pdf", exc_info=True
            )

    @staticmethod
    def get_informe_create_context(admision_id, tipo):
        try:
            admision = get_object_or_404(Admision, pk=admision_id)
            return {
                "tipo": tipo,
                "admision": admision,
                "anexo": Anexo.objects.filter(admision=admision).last(),
            }
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_informe_create_context",
                exc_info=True,
            )
            return {}

    @staticmethod
    def get_informe_update_context(informe, tipo):
        try:
            campos_a_subsanar = CampoASubsanar.objects.filter(
                informe=informe
            ).values_list("campo", flat=True)
            try:
                observacion = ObservacionGeneralInforme.objects.get(informe=informe)
            except ObservacionGeneralInforme.DoesNotExist:
                observacion = None

            return {
                "tipo": tipo,
                "admision": informe.admision,
                "comedor": informe.admision.comedor,
                "campos": InformeService.get_campos_visibles_informe(informe),
                "anexo": Anexo.objects.filter(admision=informe.admision).last(),
                "campos_a_subsanar": list(campos_a_subsanar),
                "observacion": observacion,
            }
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_informe_update_context",
                exc_info=True,
            )
            return {}

    @staticmethod
    def get_context_informe_detail(informe, tipo):
        try:
            return {
                "tipo": tipo,
                "admision": informe.admision,
                "campos": InformeService.get_campos_visibles_informe(informe),
                "pdf": InformeTecnicoPDF.objects.filter(
                    admision=informe.admision, tipo=tipo, informe_id=informe.id
                ).first(),
            }
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_context_informe_detail",
                exc_info=True,
            )
            return {}

    @staticmethod
    def procesar_revision_informe(request, tipo, informe):
        try:
            nuevo_estado = request.POST.get("estado")
            if nuevo_estado not in ["A subsanar", "Validado"]:
                return

            InformeService.actualizar_estado_informe(informe, nuevo_estado, tipo)

            if nuevo_estado == "A subsanar":
                campos_a_subsanar = request.POST.getlist("campos_a_subsanar")
                observacion = request.POST.get("observacion", "").strip()

                CampoASubsanar.objects.filter(informe=informe).delete()

                for campo in campos_a_subsanar:
                    CampoASubsanar.objects.create(informe=informe, campo=campo)

                obs_obj, _ = ObservacionGeneralInforme.objects.get_or_create(
                    informe=informe
                )
                obs_obj.texto = observacion
                obs_obj.save()
            else:
                CampoASubsanar.objects.filter(informe=informe).delete()
                ObservacionGeneralInforme.objects.filter(informe=informe).delete()
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en procesar_revision_informe",
                exc_info=True,
            )

    @staticmethod
    def guardar_campos_complementarios(informe_tecnico, campos_dict, usuario):
        try:
            informe = InformeComplementario.objects.create(
                admision=informe_tecnico.admision,
                informe_tecnico=informe_tecnico,
                creado_por=usuario,
            )
            for campo, valor in campos_dict.items():
                InformeComplementarioCampos.objects.create(
                    campo=campo, value=valor, informe_complementario=informe
                )
            return informe
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en guardar_campos_complementarios",
                exc_info=True,
            )
            return None

    @staticmethod
    def generar_y_guardar_pdf_complementario(informe_complementario):
        try:
            campos = [
                (campo.campo, campo.value)
                for campo in informe_complementario.informecomplementariocampos_set.all()
            ]
            html_string = render_to_string(
                "pdf_informe_complementario.html",
                {"informe": informe_complementario, "campos": campos},
            )
            pdf_bytes = HTML(string=html_string).write_pdf()
            nombre_archivo = f"complementario_{informe_complementario.id}.pdf"
            informe_complementario.pdf.save(
                nombre_archivo, ContentFile(pdf_bytes), save=True
            )
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en generar_y_guardar_pdf_complementario",
                exc_info=True,
            )
