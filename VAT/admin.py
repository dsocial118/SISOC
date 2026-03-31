from django.contrib import admin
from .models import (
    Centro,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
    InscripcionOferta,
    Voucher,
    VoucherRecarga,
    VoucherUso,
    VoucherLog,
    # Fase 2
    InstitucionContacto,
    AutoridadInstitucional,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    # Fase 4
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    # Fase 5
    Inscripcion,
    # Fase 6
    AsistenciaSesion,
    # Fase 7
    Evaluacion,
    ResultadoEvaluacion,
)


@admin.register(Centro)
class CentroAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_gestion", "activo")
    list_filter = ("activo", "tipo_gestion")
    search_fields = ("nombre",)
    fieldsets = (
        ("Información General", {"fields": ("nombre", "codigo", "referente")}),
        (
            "Ubicación",
            {
                "fields": (
                    "provincia",
                    "municipio",
                    "localidad",
                    "calle",
                    "numero",
                    "domicilio_actividad",
                )
            },
        ),
        ("Contacto", {"fields": ("telefono", "celular", "correo", "sitio_web")}),
        (
            "Responsable",
            {
                "fields": (
                    "nombre_referente",
                    "apellido_referente",
                    "telefono_referente",
                    "correo_referente",
                )
            },
        ),
        (
            "Clasificación",
            {"fields": ("tipo_gestion", "clase_institucion", "situacion")},
        ),
        ("Estado", {"fields": ("activo",)}),
    )


@admin.register(ModalidadInstitucional)
class ModalidadInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "fecha_creacion")
    list_filter = ("activo", "fecha_creacion")
    search_fields = ("nombre",)
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    inlines = []


class SubsectorInline(admin.TabularInline):
    model = Subsector
    extra = 1


@admin.register(Subsector)
class SubsectorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sector")
    list_filter = ("sector",)
    search_fields = ("nombre",)


@admin.register(TituloReferencia)
class TituloReferenciaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "plan_estudio", "activo")
    list_filter = ("plan_estudio", "activo")
    search_fields = (
        "nombre",
        "codigo_referencia",
        "plan_estudio__sector__nombre",
        "plan_estudio__subsector__nombre",
    )
    fieldsets = (
        (
            "Información General",
            {"fields": ("nombre", "codigo_referencia", "descripcion")},
        ),
        ("Clasificación", {"fields": ("plan_estudio",)}),
        ("Estado", {"fields": ("activo",)}),
    )


@admin.register(ModalidadCursada)
class ModalidadCursadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(PlanVersionCurricular)
class PlanVersionCurricularAdmin(admin.ModelAdmin):
    list_display = (
        "sector",
        "subsector",
        "modalidad_cursada",
        "activo",
    )
    list_filter = ("sector", "subsector", "modalidad_cursada", "activo")
    search_fields = ("sector__nombre", "subsector__nombre", "normativa")
    fieldsets = (
        (
            "Información General",
            {
                "fields": (
                    "sector",
                    "subsector",
                    "modalidad_cursada",
                )
            },
        ),
        ("Normativa y Horas", {"fields": ("normativa", "horas_reloj")}),
        ("Niveles", {"fields": ("nivel_requerido", "nivel_certifica")}),
        ("Estado", {"fields": ("activo",)}),
    )


@admin.register(InscripcionOferta)
class InscripcionOfertaAdmin(admin.ModelAdmin):
    list_display = ("ciudadano", "oferta", "estado", "fecha_inscripcion")
    list_filter = ("estado", "fecha_inscripcion")
    search_fields = ("ciudadano__nombre", "ciudadano__apellido")
    fieldsets = (
        ("Información", {"fields": ("oferta", "ciudadano", "estado")}),
        (
            "Auditoría",
            {
                "fields": ("inscrito_por", "fecha_inscripcion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("fecha_inscripcion", "fecha_modificacion", "inscrito_por")


# ============================================================================
# VOUCHER ADMIN REGISTRATIONS
# ============================================================================


class VoucherRecargaInline(admin.TabularInline):
    model = VoucherRecarga
    extra = 0
    readonly_fields = ("fecha_recarga",)
    fields = ("cantidad", "motivo", "autorizado_por", "fecha_recarga")


class VoucherUsoInline(admin.TabularInline):
    model = VoucherUso
    extra = 0
    readonly_fields = ("fecha_uso",)
    fields = ("inscripcion_oferta", "cantidad_usada", "fecha_uso")


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "ciudadano",
        "cantidad_disponible",
        "cantidad_usada",
        "cantidad_inicial",
        "estado",
        "fecha_vencimiento",
    )
    list_filter = ("estado", "programa", "fecha_vencimiento", "fecha_asignacion")
    search_fields = ("ciudadano__nombre", "ciudadano__apellido", "ciudadano__documento")
    readonly_fields = ("fecha_asignacion", "fecha_creacion", "fecha_modificacion")
    inlines = [VoucherRecargaInline, VoucherUsoInline]
    fieldsets = (
        (
            "Información General",
            {
                "fields": (
                    "ciudadano",
                    "programa",
                    "estado",
                )
            },
        ),
        (
            "Cuotas",
            {
                "fields": (
                    "cantidad_inicial",
                    "cantidad_usada",
                    "cantidad_disponible",
                )
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "fecha_asignacion",
                    "fecha_vencimiento",
                )
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(VoucherRecarga)
class VoucherRecargaAdmin(admin.ModelAdmin):
    list_display = ("voucher", "cantidad", "motivo", "fecha_recarga", "autorizado_por")
    list_filter = ("motivo", "fecha_recarga")
    search_fields = (
        "voucher__ciudadano__nombre",
        "voucher__ciudadano__apellido",
    )
    readonly_fields = ("fecha_recarga",)
    fieldsets = (
        ("Información", {"fields": ("voucher", "cantidad", "motivo")}),
        ("Autorización", {"fields": ("autorizado_por",)}),
        ("Auditoría", {"fields": ("fecha_recarga",), "classes": ("collapse",)}),
    )


@admin.register(VoucherUso)
class VoucherUsoAdmin(admin.ModelAdmin):
    list_display = ("voucher", "inscripcion_oferta", "cantidad_usada", "fecha_uso")
    list_filter = ("fecha_uso",)
    search_fields = (
        "voucher__ciudadano__nombre",
        "voucher__ciudadano__apellido",
    )
    readonly_fields = ("fecha_uso",)
    fieldsets = (
        (
            "Información",
            {"fields": ("voucher", "inscripcion_oferta", "cantidad_usada")},
        ),
        ("Auditoría", {"fields": ("fecha_uso",), "classes": ("collapse",)}),
    )


@admin.register(VoucherLog)
class VoucherLogAdmin(admin.ModelAdmin):
    list_display = (
        "voucher",
        "tipo_evento",
        "cantidad_afectada",
        "fecha_evento",
        "usuario",
    )
    list_filter = ("tipo_evento", "fecha_evento")
    search_fields = (
        "voucher__ciudadano__nombre",
        "voucher__ciudadano__apellido",
    )
    readonly_fields = (
        "fecha_evento",
        "voucher",
        "tipo_evento",
        "cantidad_afectada",
        "usuario",
        "detalles",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = (
        (
            "Evento",
            {
                "fields": (
                    "voucher",
                    "tipo_evento",
                    "cantidad_afectada",
                )
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("usuario", "fecha_evento", "detalles"),
                "classes": ("collapse",),
            },
        ),
    )


# ============================================================================
# FASE 2: INSTITUCIÓN - CONTACTOS E IDENTIFICADORES
# ============================================================================


@admin.register(InstitucionContacto)
class InstitucionContactoAdmin(admin.ModelAdmin):
    list_display = (
        "centro",
        "tipo",
        "valor",
        "es_principal",
        "vigencia_desde",
        "vigencia_hasta",
    )
    list_filter = ("tipo", "es_principal", "vigencia_desde")
    search_fields = ("centro__nombre", "valor")
    readonly_fields = ("vigencia_desde", "fecha_creacion", "fecha_modificacion")


@admin.register(AutoridadInstitucional)
class AutoridadInstitucionalAdmin(admin.ModelAdmin):
    list_display = (
        "centro",
        "nombre_completo",
        "cargo",
        "dni",
        "es_actual",
        "vigencia_desde",
    )
    list_filter = ("es_actual", "vigencia_desde")
    search_fields = ("centro__nombre", "nombre_completo", "dni")
    readonly_fields = ("vigencia_desde", "fecha_creacion", "fecha_modificacion")


@admin.register(InstitucionIdentificadorHist)
class InstitucionIdentificadorHistAdmin(admin.ModelAdmin):
    list_display = (
        "centro",
        "tipo_identificador",
        "valor_identificador",
        "rol_institucional",
        "es_actual",
    )
    list_filter = ("tipo_identificador", "rol_institucional", "es_actual")
    search_fields = ("centro__nombre", "valor_identificador")
    readonly_fields = ("vigencia_desde", "fecha_creacion", "fecha_modificacion")


@admin.register(InstitucionUbicacion)
class InstitucionUbicacionAdmin(admin.ModelAdmin):
    list_display = ("centro", "localidad", "rol_ubicacion", "es_principal", "domicilio")
    list_filter = ("rol_ubicacion", "es_principal")
    search_fields = ("centro__nombre", "localidad__nombre", "domicilio")
    readonly_fields = ("vigencia_desde", "fecha_creacion", "fecha_modificacion")


# ============================================================================
# FASE 4: OFERTA INSTITUCIONAL - COMISIONES
# ============================================================================


class ComisionInline(admin.TabularInline):
    model = Comision
    extra = 0
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


@admin.register(OfertaInstitucional)
class OfertaInstitucionalAdmin(admin.ModelAdmin):
    list_display = (
        "centro",
        "plan_curricular",
        "ciclo_lectivo",
        "estado",
        "usa_voucher",
    )
    list_filter = ("estado", "centro", "ciclo_lectivo", "usa_voucher")
    search_fields = ("centro__nombre", "plan_curricular__titulos__nombre")
    inlines = [ComisionInline]
    readonly_fields = ("fecha_creacion", "fecha_modificacion")
    fieldsets = (
        ("Información", {"fields": ("centro", "plan_curricular", "programa")}),
        ("Detalles", {"fields": ("nombre_local", "ciclo_lectivo", "plan_externo_id")}),
        (
            "Estado y Voucher",
            {"fields": ("estado", "costo", "usa_voucher", "fecha_publicacion")},
        ),
        (
            "Auditoría",
            {
                "fields": ("observaciones", "fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )


class ComisionHorarioInline(admin.TabularInline):
    model = ComisionHorario
    extra = 0
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_comision",
        "nombre",
        "oferta",
        "cupo",
        "estado",
        "fecha_inicio",
    )
    list_filter = ("estado", "oferta__centro", "fecha_inicio")
    search_fields = ("codigo_comision", "nombre", "oferta__centro__nombre")
    inlines = [ComisionHorarioInline]
    readonly_fields = ("fecha_creacion", "fecha_modificacion")
    fieldsets = (
        (
            "Información",
            {"fields": ("oferta", "ubicacion", "codigo_comision", "nombre")},
        ),
        ("Período", {"fields": ("fecha_inicio", "fecha_fin")}),
        ("Capacidad", {"fields": ("cupo", "estado")}),
        (
            "Auditoría",
            {
                "fields": ("observaciones", "fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ComisionHorario)
class ComisionHorarioAdmin(admin.ModelAdmin):
    list_display = (
        "comision",
        "dia_semana",
        "hora_desde",
        "hora_hasta",
        "aula_espacio",
        "vigente",
    )
    list_filter = ("vigente", "dia_semana")
    search_fields = ("comision__codigo_comision", "aula_espacio")
    readonly_fields = ("fecha_creacion", "fecha_modificacion")


# ============================================================================
# FASE 5: INSCRIPCIÓN
# ============================================================================


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("ciudadano", "comision", "estado", "fecha_inscripcion", "programa")
    list_filter = (
        "estado",
        "comision__oferta__centro",
        "fecha_inscripcion",
        "programa",
    )
    search_fields = (
        "ciudadano__nombre",
        "ciudadano__apellido",
        "comision__codigo_comision",
    )
    readonly_fields = ("fecha_inscripcion", "fecha_creacion", "fecha_modificacion")
    fieldsets = (
        ("Información", {"fields": ("ciudadano", "comision", "programa")}),
        (
            "Estado",
            {"fields": ("estado", "origen_canal", "fecha_validacion_presencial")},
        ),
        (
            "Auditoría",
            {
                "fields": (
                    "observaciones",
                    "fecha_inscripcion",
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )


# ============================================================================
# FASE 6: ASISTENCIA
# ============================================================================


@admin.register(AsistenciaSesion)
class AsistenciaSesionAdmin(admin.ModelAdmin):
    list_display = (
        "sesion",
        "inscripcion",
        "presente",
        "registrado_por",
        "fecha_registro",
    )
    list_filter = ("presente", "sesion__comision", "fecha_registro")
    search_fields = (
        "inscripcion__ciudadano__nombre",
        "inscripcion__ciudadano__apellido",
        "sesion__comision__codigo_comision",
    )
    readonly_fields = ("fecha_registro",)


# ============================================================================
# FASE 7: EVALUACIONES
# ============================================================================


class ResultadoEvaluacionInline(admin.TabularInline):
    model = ResultadoEvaluacion
    extra = 0
    readonly_fields = ("fecha_registro", "fecha_creacion", "fecha_modificacion")
    fields = ("inscripcion", "calificacion", "aprobo", "registrado_por")


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("comision", "nombre", "tipo", "fecha", "es_final", "ponderacion")
    list_filter = ("tipo", "es_final", "comision__oferta__centro")
    search_fields = ("nombre", "comision__codigo_comision")
    inlines = [ResultadoEvaluacionInline]
    readonly_fields = ("fecha_creacion", "fecha_modificacion")
    fieldsets = (
        ("Información", {"fields": ("comision", "nombre", "tipo", "es_final")}),
        (
            "Detalles",
            {"fields": ("fecha", "descripcion", "ponderacion", "observaciones")},
        ),
        (
            "Auditoría",
            {
                "fields": ("fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ResultadoEvaluacion)
class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "inscripcion",
        "evaluacion",
        "calificacion",
        "aprobo",
        "fecha_registro",
        "registrado_por",
    )
    list_filter = ("aprobo", "evaluacion__tipo", "fecha_registro")
    search_fields = (
        "inscripcion__persona__nombre",
        "inscripcion__persona__apellido",
        "evaluacion__nombre",
    )
    readonly_fields = ("fecha_registro", "fecha_creacion", "fecha_modificacion")
    fieldsets = (
        ("Información", {"fields": ("evaluacion", "inscripcion")}),
        ("Resultados", {"fields": ("calificacion", "aprobo", "observaciones")}),
        (
            "Auditoría",
            {
                "fields": (
                    "registrado_por",
                    "fecha_registro",
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
                "classes": ("collapse",),
            },
        ),
    )
