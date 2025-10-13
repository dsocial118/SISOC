from docxtpl import DocxTemplate
from django.conf import settings
import os
import io


class DocxTemplateService:
    """Servicio para generar documentos DOCX usando templates."""
    
    @staticmethod
    def generar_docx_desde_template(template_name, context):
        """
        Genera un documento DOCX desde un template.
        
        Args:
            template_name (str): Nombre del archivo template (ej: 'informe_tecnico.docx')
            context (dict): Datos para renderizar en el template
            
        Returns:
            io.BytesIO: Buffer con el documento generado
        """
        template_path = os.path.join(
            settings.BASE_DIR, 
            'admisiones', 
            'templates', 
            'docx', 
            template_name
        )
        
        print(f"DEBUG: Buscando template en: {template_path}")
        
        if not os.path.exists(template_path):
            print(f"DEBUG ERROR: Template no encontrado en: {template_path}")
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
        
        print(f"DEBUG: Template encontrado: {template_path}")
        
        try:
            # Cargar template
            doc = DocxTemplate(template_path)
            print(f"DEBUG: Template cargado exitosamente")
        except Exception as e:
            print(f"DEBUG ERROR: Error cargando template: {str(e)}")
            raise
        
        # Renderizar con contexto
        doc.render(context)
        
        # Guardar en buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def preparar_contexto_informe_tecnico(informe):
        """Prepara el contexto para el template de informe técnico."""
        from ..utils import generar_texto_comidas
        
        prestaciones = [
            {'dia': 'Lunes', 'desayuno': informe.solicitudes_desayuno_lunes, 'almuerzo': informe.solicitudes_almuerzo_lunes, 'merienda': informe.solicitudes_merienda_lunes, 'cena': informe.solicitudes_cena_lunes},
            {'dia': 'Martes', 'desayuno': informe.solicitudes_desayuno_martes, 'almuerzo': informe.solicitudes_almuerzo_martes, 'merienda': informe.solicitudes_merienda_martes, 'cena': informe.solicitudes_cena_martes},
            {'dia': 'Miércoles', 'desayuno': informe.solicitudes_desayuno_miercoles, 'almuerzo': informe.solicitudes_almuerzo_miercoles, 'merienda': informe.solicitudes_merienda_miercoles, 'cena': informe.solicitudes_cena_miercoles},
            {'dia': 'Jueves', 'desayuno': informe.solicitudes_desayuno_jueves, 'almuerzo': informe.solicitudes_almuerzo_jueves, 'merienda': informe.solicitudes_merienda_jueves, 'cena': informe.solicitudes_cena_jueves},
            {'dia': 'Viernes', 'desayuno': informe.solicitudes_desayuno_viernes, 'almuerzo': informe.solicitudes_almuerzo_viernes, 'merienda': informe.solicitudes_merienda_viernes, 'cena': informe.solicitudes_cena_viernes},
            {'dia': 'Sábado', 'desayuno': informe.solicitudes_desayuno_sabado, 'almuerzo': informe.solicitudes_almuerzo_sabado, 'merienda': informe.solicitudes_merienda_sabado, 'cena': informe.solicitudes_cena_sabado},
            {'dia': 'Domingo', 'desayuno': informe.solicitudes_desayuno_domingo, 'almuerzo': informe.solicitudes_almuerzo_domingo, 'merienda': informe.solicitudes_merienda_domingo, 'cena': informe.solicitudes_cena_domingo},
        ]
        
        return {
            'informe': informe,  # Incluir el objeto informe completo
            'texto_comidas': generar_texto_comidas(informe),  # Incluir texto de comidas
            'tipo': informe.tipo,
            'expediente_nro': informe.expediente_nro,
            'nombre_organizacion': informe.nombre_organizacion,
            'domicilio_organizacion': informe.domicilio_organizacion,
            'localidad_organizacion': informe.localidad_organizacion,
            'partido_organizacion': informe.partido_organizacion,
            'provincia_organizacion': informe.provincia_organizacion,
            'fecha_actual': informe.admision.creado.strftime('%d/%m/%Y'),
            'tipo_espacio': informe.tipo_espacio,
            'nombre_espacio': informe.nombre_espacio,
            'domicilio_espacio': informe.domicilio_espacio,
            'barrio_espacio': informe.barrio_espacio,
            'responsable_nombre': informe.responsable_tarjeta_nombre,
            'responsable_dni': informe.responsable_tarjeta_dni,
            'responsable_domicilio': informe.responsable_tarjeta_domicilio,
            'prestaciones': prestaciones,
            'total_desayunos': sum(p['desayuno'] for p in prestaciones),
            'total_almuerzos': sum(p['almuerzo'] for p in prestaciones),
            'total_meriendas': sum(p['merienda'] for p in prestaciones),
            'total_cenas': sum(p['cena'] for p in prestaciones),
            'conclusiones': getattr(informe, 'conclusiones', ''),
        }

    @staticmethod
    def preparar_contexto_admision(admision):
        """Prepara el contexto específico para documentos de admisión"""
        from ..models.admisiones import ArchivoAdmision, InformeTecnico
        
        # Obtener documentos
        documentos = []
        archivos = ArchivoAdmision.objects.filter(admision=admision)
        for archivo in archivos:
            documentos.append({
                'nombre': archivo.documentacion.nombre if archivo.documentacion else archivo.nombre_personalizado,
                'estado': archivo.estado,
                'observaciones': archivo.observaciones
            })
        
        # Obtener informe técnico
        informe_tecnico = InformeTecnico.objects.filter(admision=admision).first()
        
        # Obtener historial (últimos 10 cambios)
        historial = admision.historial.all().order_by('-fecha')[:10]
        
        return {
            'admision': admision,
            'comedor': admision.comedor,
            'documentos': documentos,
            'informe_tecnico': informe_tecnico,
            'historial': historial,
            'fecha_actual': admision.creado.strftime('%d/%m/%Y'),
            'fecha_generacion': admision.creado.strftime('%d/%m/%Y %H:%M'),
        }

    @staticmethod
    def preparar_contexto_proyecto_convenio(admision):
        """Prepara el contexto específico para proyectos de convenio"""
        from ..models.admisiones import FormularioProyectoDeConvenio, InformeTecnico
        
        formulario = FormularioProyectoDeConvenio.objects.filter(admision=admision).first()
        informe = InformeTecnico.objects.filter(admision=admision).first()
        
        return {
            'admision': admision,
            'comedor': admision.comedor,
            'formulario': formulario,
            'informe': informe,
            'fecha_actual': admision.creado.strftime('%d/%m/%Y'),
            'fecha_generacion': admision.creado.strftime('%d/%m/%Y %H:%M'),
        }

    @staticmethod
    def preparar_contexto_proyecto_disposicion(admision):
        """Prepara el contexto específico para proyectos de disposición"""
        from ..models.admisiones import FormularioProyectoDisposicion, FormularioProyectoDeConvenio, InformeTecnico
        
        formulario = FormularioProyectoDisposicion.objects.filter(admision=admision).first()
        proyecto_convenio = FormularioProyectoDeConvenio.objects.filter(admision=admision).first()
        informe = InformeTecnico.objects.filter(admision=admision).first()
        
        return {
            'admision': admision,
            'comedor': admision.comedor,
            'formulario': formulario,
            'proyecto_convenio': proyecto_convenio,
            'informe': informe,
            'fecha_actual': admision.creado.strftime('%d/%m/%Y'),
            'fecha_generacion': admision.creado.strftime('%d/%m/%Y %H:%M'),
        }