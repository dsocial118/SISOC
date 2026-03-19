import logging
from datetime import datetime, date

from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo

logger = logging.getLogger("django")


class CiudadanoService:
    @staticmethod
    def _normalizar_texto_opcional(raw):
        if raw in (None, ""):
            return None
        value = str(raw).strip()
        return value or None

    @staticmethod
    def _to_date(value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        s = str(value).strip()
        if " " in s:
            s = s.split(" ")[0]
        s = s.replace("/", "-")
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError as exc:
                if "day is out of range" in str(exc):
                    raise ValidationError(f"Fecha inválida: {value}")
            except Exception:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise ValidationError(f"Fecha de nacimiento inválida: {value}") from exc

    @staticmethod
    def _normalizar_tipo_documento(raw) -> str:
        default = Ciudadano.DOCUMENTO_DNI
        if raw in (None, ""):
            return default
        value = str(raw).strip().upper()
        opciones = {choice[0]: choice[0] for choice in Ciudadano.DOCUMENTO_CHOICES}
        for key in opciones:
            if value in {key, key.upper(), key.lower()}:
                return key
        raise ValidationError(f"Tipo de documento inválido: {raw}")

    @staticmethod
    def _resolver_sexo(raw):
        if raw in (None, ""):
            return None
        raw_str = str(raw).strip()
        if raw_str.isdigit():
            return Sexo.objects.filter(pk=int(raw_str)).first()
        return Sexo.objects.filter(sexo__iexact=raw_str).first()

    @staticmethod
    def _resolver_nacionalidad(raw):
        if raw in (None, ""):
            return None
        raw_str = str(raw).strip()
        if raw_str.isdigit():
            return Nacionalidad.objects.filter(pk=int(raw_str)).first()
        return Nacionalidad.objects.filter(nacionalidad__iexact=raw_str).first()

    @staticmethod
    def _resolver_provincia(raw):
        if raw in (None, ""):
            return None
        try:
            return Provincia.objects.get(pk=int(str(raw).strip()))
        except (Provincia.DoesNotExist, ValueError) as exc:
            raise ValidationError(f"Provincia inválida: {raw}") from exc

    @staticmethod
    def _resolver_municipio(raw, provincia):
        if raw in (None, ""):
            return None
        if provincia is None:
            raise ValidationError(
                "Debe indicar la provincia para validar el municipio."
            )
        try:
            return Municipio.objects.get(pk=int(str(raw).strip()), provincia=provincia)
        except (Municipio.DoesNotExist, ValueError) as exc:
            raise ValidationError("Municipio inválido para la provincia dada.") from exc

    @staticmethod
    def _resolver_localidad(raw, municipio):
        if raw in (None, ""):
            return None
        try:
            localidad_id = int(str(raw).strip())
            if municipio is None:
                # Si no hay municipio, buscar localidad solo por ID
                return Localidad.objects.filter(pk=localidad_id).first()
            return Localidad.objects.get(pk=localidad_id, municipio=municipio)
        except (Localidad.DoesNotExist, ValueError) as exc:
            raise ValidationError("Localidad inválida para el municipio dado.") from exc

    @staticmethod
    def get_or_create_ciudadano(
        datos: dict, usuario=None, expediente=None
    ) -> Ciudadano:
        """Crea o actualiza un ciudadano con los datos básicos recibidos."""

        tipo_documento = CiudadanoService._normalizar_tipo_documento(
            datos.get("tipo_documento")
        )
        documento = datos.get("documento")
        if documento in (None, ""):
            raise ValidationError("El número de documento es obligatorio.")

        sexo = CiudadanoService._resolver_sexo(datos.get("sexo"))
        if datos.get("sexo") not in (None, "") and sexo is None:
            raise ValidationError(f"Sexo inválido: {datos.get('sexo')}")

        provincia = CiudadanoService._resolver_provincia(datos.get("provincia"))
        municipio = CiudadanoService._resolver_municipio(
            datos.get("municipio"), provincia
        )
        localidad = CiudadanoService._resolver_localidad(
            datos.get("localidad"), municipio
        )

        fecha_nacimiento = CiudadanoService._to_date(datos.get("fecha_nacimiento"))
        nombre = datos.get("nombre", "").strip()
        apellido = datos.get("apellido", "").strip()
        nacionalidad = CiudadanoService._resolver_nacionalidad(
            datos.get("nacionalidad")
        )
        if datos.get("nacionalidad") not in (None, "") and nacionalidad is None:
            raise ValidationError(f"Nacionalidad invalida: {datos.get('nacionalidad')}")
        calle = CiudadanoService._normalizar_texto_opcional(datos.get("calle"))
        altura = CiudadanoService._normalizar_texto_opcional(datos.get("altura"))
        codigo_postal = CiudadanoService._normalizar_texto_opcional(
            datos.get("codigo_postal")
        )
        telefono = CiudadanoService._normalizar_texto_opcional(datos.get("telefono"))
        email = CiudadanoService._normalizar_texto_opcional(datos.get("email"))
        barrio = CiudadanoService._normalizar_texto_opcional(datos.get("barrio"))
        piso_departamento = CiudadanoService._normalizar_texto_opcional(
            datos.get("piso_departamento")
        )

        ciudadano = Ciudadano.objects.filter(
            tipo_documento=tipo_documento, documento=documento
        ).first()

        created = False
        if ciudadano is None:
            try:
                with transaction.atomic():
                    ciudadano = Ciudadano.objects.create(
                        tipo_documento=tipo_documento,
                        documento=documento,
                        nombre=nombre,
                        apellido=apellido,
                        fecha_nacimiento=fecha_nacimiento,
                        sexo=sexo,
                        nacionalidad=nacionalidad,
                        provincia=provincia,
                        municipio=municipio,
                        localidad=localidad,
                        calle=calle,
                        altura=altura,
                        barrio=barrio,
                        piso_departamento=piso_departamento,
                        codigo_postal=codigo_postal,
                        telefono=telefono,
                        email=email,
                    )
                    created = True
                    logger.info("Ciudadano creado: %s", ciudadano.pk)

                    # Crear registro en CiudadanoPrograma con programa ID 3 (Celiaquia)
                    from ciudadanos.models import CiudadanoPrograma
                    from core.models import Programa

                    try:
                        programa = Programa.objects.get(pk=3)
                        CiudadanoPrograma.objects.get_or_create(
                            ciudadano=ciudadano,
                            programas=programa,
                            defaults={"creado_por": usuario},
                        )
                    except Programa.DoesNotExist:
                        logger.warning("Programa con ID 3 no existe")
                    except Exception as e:
                        logger.error("Error creando CiudadanoPrograma: %s", e)

            except IntegrityError:
                ciudadano = Ciudadano.objects.filter(
                    tipo_documento=tipo_documento, documento=documento
                ).first()
                if ciudadano is None:
                    raise
        else:
            updates = []
            if not ciudadano.sexo_id and sexo:
                ciudadano.sexo = sexo
                updates.append("sexo")
            if not ciudadano.nombre and nombre:
                ciudadano.nombre = nombre
                updates.append("nombre")
            if not ciudadano.apellido and apellido:
                ciudadano.apellido = apellido
                updates.append("apellido")
            if not ciudadano.fecha_nacimiento and fecha_nacimiento:
                ciudadano.fecha_nacimiento = fecha_nacimiento
                updates.append("fecha_nacimiento")
            if not ciudadano.nacionalidad_id and nacionalidad:
                ciudadano.nacionalidad = nacionalidad
                updates.append("nacionalidad")
            if not ciudadano.provincia_id and provincia:
                ciudadano.provincia = provincia
                updates.append("provincia")
            if not ciudadano.municipio_id and municipio:
                ciudadano.municipio = municipio
                updates.append("municipio")
            if not ciudadano.localidad_id and localidad:
                ciudadano.localidad = localidad
                updates.append("localidad")
            for field_name, raw_value in {
                "calle": calle,
                "altura": altura,
                "barrio": barrio,
                "piso_departamento": piso_departamento,
                "codigo_postal": codigo_postal,
                "telefono": telefono,
                "email": email,
            }.items():
                normalized_value = CiudadanoService._normalizar_texto_opcional(
                    raw_value
                )
                current_value = getattr(ciudadano, field_name)
                if current_value in (None, ""):
                    if normalized_value is not None:
                        setattr(ciudadano, field_name, normalized_value)
                        updates.append(field_name)
                    elif current_value == "":
                        setattr(ciudadano, field_name, None)
                        updates.append(field_name)
            if updates:
                ciudadano.save(update_fields=updates)
                logger.debug("Ciudadano %s actualizado (%s)", ciudadano.pk, updates)

        return ciudadano
