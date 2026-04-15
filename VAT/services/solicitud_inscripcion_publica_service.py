from VAT.models import SolicitudInscripcionPublica


class SolicitudInscripcionPublicaService:
    @staticmethod
    def crear_desde_vat_web(
        *, comision, programa=None, datos_postulante=None, observaciones=""
    ):
        if not getattr(getattr(comision, "curso", None), "inscripcion_libre", False):
            raise ValueError(
                "La comisión indicada no admite solicitudes públicas sin ciudadano."
            )

        return SolicitudInscripcionPublica.objects.create(
            comision_curso=comision,
            programa=programa,
            origen_canal="front_publico",
            datos_postulante=datos_postulante or {},
            observaciones=observaciones or "",
        )

    @staticmethod
    def registrar_conversion_desde_vat_web(
        *,
        comision,
        ciudadano,
        inscripcion,
        programa=None,
        datos_postulante=None,
        observaciones="",
    ):
        if not getattr(getattr(comision, "curso", None), "inscripcion_libre", False):
            raise ValueError(
                "La comisión indicada no admite solicitudes públicas sin ciudadano."
            )

        return SolicitudInscripcionPublica.objects.create(
            comision_curso=comision,
            ciudadano=ciudadano,
            programa=programa,
            inscripcion=inscripcion,
            estado="convertida",
            origen_canal="front_publico",
            datos_postulante=datos_postulante or {},
            observaciones=observaciones or "",
        )
