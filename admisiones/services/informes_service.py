from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile

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
        return (
            InformeTecnicoJuridicoForm if tipo == "juridico" else InformeTecnicoBaseForm
        )

    @staticmethod
    def get_tipo_from_kwargs(kwargs):
        return kwargs.get("tipo", "base")

    @staticmethod
    def get_queryset_informe_por_tipo(tipo):
        return InformeTecnico.objects.filter(tipo=tipo)

    @staticmethod
    def get_admision_y_tipo_from_kwargs(kwargs):
        """
        Extrae y retorna admisión y tipo desde kwargs.

        Returns:
            (Admision, str)
        """
        tipo = kwargs.get("tipo", "base")
        admision_id = kwargs.get("admision_id")
        admision = get_object_or_404(Admision, pk=admision_id)
        return admision, tipo

    @staticmethod
    def verificar_estado_para_revision(informe):
        """Resetear observaciones y dejar el informe listo para revisión.

        Args:
            informe (InformeTecnico): Informe a modificar.

        Returns:
            None
        """
        if informe.estado != "Validado":
            CampoASubsanar.objects.filter(informe=informe).delete()
            ObservacionGeneralInforme.objects.filter(informe=informe).delete()
            informe.estado = "Para revision"

    @staticmethod
    def get_campos_visibles_informe(informe):
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

    @staticmethod
    def preparar_informe_para_creacion(instance, admision_id):
        instance.admision_id = admision_id
        instance.estado = "Para revision"

    @staticmethod
    def get_informe_por_tipo_y_pk(tipo, pk):
        return get_object_or_404(InformeTecnico, tipo=tipo, pk=pk)

    @staticmethod
    def actualizar_estado_informe(informe, nuevo_estado, tipo=None):
        informe.estado = nuevo_estado
        informe.save()

        if nuevo_estado == "Validado":
            InformeService.generar_y_guardar_pdf(informe, tipo)

    @staticmethod
    def generar_y_guardar_pdf(informe, tipo):
        anexo = Anexo.objects.filter(admision=informe.admision).first()

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

    @staticmethod
    def get_informe_create_context(admision_id, tipo):
        admision = get_object_or_404(Admision, pk=admision_id)
        return {
            "tipo": tipo,
            "admision": admision,
            "anexo": admision.anexo if hasattr(admision, "anexo") else None,
        }

    @staticmethod
    def get_informe_update_context(informe, tipo):
        campos_a_subsanar = CampoASubsanar.objects.filter(informe=informe).values_list(
            "campo", flat=True
        )
        try:
            observacion = ObservacionGeneralInforme.objects.get(informe=informe)
        except ObservacionGeneralInforme.DoesNotExist:
            observacion = None

        return {
            "tipo": tipo,
            "admision": informe.admision,
            "comedor": informe.admision.comedor,
            "campos": InformeService.get_campos_visibles_informe(informe),
            "anexo": (
                informe.admision.anexo if hasattr(informe.admision, "anexo") else None
            ),
            "campos_a_subsanar": list(campos_a_subsanar),
            "observacion": observacion,
        }

    @staticmethod
    def get_context_informe_detail(informe, tipo):
        return {
            "tipo": tipo,
            "admision": informe.admision,
            "campos": InformeService.get_campos_visibles_informe(informe),
            "pdf": InformeTecnicoPDF.objects.filter(
                admision=informe.admision, tipo=tipo, informe_id=informe.id
            ).first(),
        }

    @staticmethod
    def procesar_revision_informe(request, tipo, informe):
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

    @staticmethod
    def guardar_campos_complementarios(informe_tecnico, campos_dict, usuario):
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

    @staticmethod
    def generar_y_guardar_pdf_complementario(informe_complementario):
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
