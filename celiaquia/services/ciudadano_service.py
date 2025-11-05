import logging
from datetime import datetime, date
from functools import lru_cache

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Q

from ciudadanos.models import (
    Ciudadano,
    CiudadanoPrograma,
    HistorialCiudadanoProgramas,
    TipoDocumento,
    Sexo,
    Nacionalidad,
    Provincia,
    Municipio,
    Localidad,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
)

from celiaquia.models import ExpedienteCiudadano

logger = logging.getLogger("django")


@lru_cache(maxsize=1)
def _tipo_doc_por_defecto():
    """Retorna el TipoDocumento por defecto (DNI).

    Se cachea para evitar consultas repetidas. Si el registro no existe
    se lanza un ValidationError.
    """

    try:
        return TipoDocumento.objects.get(tipo__iexact="DNI")
    except TipoDocumento.DoesNotExist as exc:
        raise ValidationError("Falta TipoDocumento por defecto (DNI)") from exc


class CiudadanoService:
    @staticmethod
    def _to_date(value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        # datetime -> date
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        s = str(value).strip()
        # cortar hora si viene "YYYY-MM-DD HH:MM:SS"
        if " " in s:
            s = s.split(" ")[0]
        s = s.replace("/", "-")
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                parsed_date = datetime.strptime(s, fmt).date()
                # Validar fechas imposibles como 31/11
                if parsed_date.strftime(fmt) != s:
                    raise ValidationError(f"Fecha inválida: {value}")
                return parsed_date
            except ValueError as e:
                if "day is out of range" in str(e):
                    raise ValidationError(f"Fecha inválida: {value}")
                continue
            except Exception:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            raise ValidationError(f"Fecha de nacimiento inválida: {value}")

    @staticmethod
    def _tipo_doc_por_defecto() -> TipoDocumento:
        td = TipoDocumento.objects.filter(tipo__iexact="DNI").first()
        if td is None:
            raise ValidationError("No se encontró tipo de documento por defecto.")
        return td

    @staticmethod
    def get_or_create_ciudadano(
        datos: dict, usuario=None, expediente=None, programa_id=3
    ) -> Ciudadano:
        """
        - Busca o crea un Ciudadano usando la clave real (tipo_documento + documento).
        - Inicializa dimensiones si es nuevo.
        - Si se pasa `expediente`, primero valida si existe el legajo (ExpedienteCiudadano);
          si existe, asegura el registro en CiudadanoPrograma (lo crea si no está).
        - Si NO se pasa `expediente`, mantiene la lógica previa: intenta asignar programa.
        - `sexo` se identifica por nombre, mientras que `provincia`, `municipio` y
          `localidad` se reciben por ID y se verifica su correspondencia jerárquica.
        """
        # 1) Resolver FK TipoDocumento
        raw_td = datos.get("tipo_documento")
        if raw_td in (None, ""):
            td = CiudadanoService._tipo_doc_por_defecto()
        else:
            td = None
            raw_td_str = str(raw_td).strip()
            try:
                td = TipoDocumento.objects.get(pk=int(raw_td_str))
            except (TipoDocumento.DoesNotExist, ValueError):
                filtro = {"tipo__iexact": raw_td_str}
                if hasattr(TipoDocumento, "codigo"):
                    td = TipoDocumento.objects.filter(
                        Q(**filtro) | Q(codigo__iexact=raw_td_str)
                    ).first()
                else:
                    td = TipoDocumento.objects.filter(**filtro).first()
            if td is None:
                raise ValidationError(f"Tipo de documento inválido: {raw_td}")

        # 2) Resolver FK Sexo (por nombre o ID)
        raw_sex = datos.get("sexo")
        sx = None
        if raw_sex not in (None, ""):
            raw_sex_str = str(raw_sex).strip()
            if raw_sex_str.isdigit():
                sx = Sexo.objects.filter(pk=int(raw_sex_str)).first()
            else:
                sx = Sexo.objects.filter(sexo__iexact=raw_sex_str).first()
            if sx is None:
                raise ValidationError(f"Sexo inválido: {raw_sex}")

        # 3) Resolver FK Nacionalidad
        raw_nat = datos.get("nacionalidad")
        nac = None
        if raw_nat not in (None, ""):
            raw_nat_str = str(raw_nat).strip()
            try:
                nac = Nacionalidad.objects.get(pk=int(raw_nat_str))
            except (Nacionalidad.DoesNotExist, ValueError):
                nac = Nacionalidad.objects.filter(
                    nacionalidad__iexact=raw_nat_str
                ).first()

        # 4) Resolver FK Provincia (por ID)
        raw_prov = datos.get("provincia")
        prov = None
        if raw_prov not in (None, ""):
            try:
                prov = Provincia.objects.get(pk=int(str(raw_prov).strip()))
            except (Provincia.DoesNotExist, ValueError) as exc:
                raise ValidationError(f"Provincia inválida: {raw_prov}") from exc

        # 5) Resolver FK Municipio restringido por provincia (ID obligatorio)
        raw_mun = datos.get("municipio")
        mun = None
        if raw_mun not in (None, ""):
            if prov is None:
                raise ValidationError(
                    "Se debe especificar provincia para validar municipio."
                )
            try:
                mun = Municipio.objects.get(
                    pk=int(str(raw_mun).strip()), provincia=prov
                )
            except (Municipio.DoesNotExist, ValueError) as exc:
                raise ValidationError(
                    f"Municipio inválido para la provincia {prov}"
                ) from exc

        # 6) Resolver FK Localidad restringido por municipio (ID obligatorio)
        raw_loc = datos.get("localidad")
        loc = None
        if raw_loc not in (None, ""):
            if mun is None:
                raise ValidationError(
                    "Se debe especificar municipio para validar localidad."
                )
            try:
                loc = Localidad.objects.get(pk=int(str(raw_loc).strip()), municipio=mun)
            except (Localidad.DoesNotExist, ValueError) as exc:
                raise ValidationError(
                    f"Localidad inválida para el municipio {mun}"
                ) from exc

        # 7) Normalizar fecha de nacimiento
        fecha_nac = CiudadanoService._to_date(datos.get("fecha_nacimiento"))

        # 8) Datos básicos
        doc = datos.get("documento")
        nom = datos.get("nombre")
        ape = datos.get("apellido")
        calle = datos.get("calle")
        altura = datos.get("altura")
        codigo_postal = datos.get("codigo_postal")
        telefono = datos.get("telefono")
        email = datos.get("email")

        if doc in (None, ""):
            raise ValidationError("El número de documento es obligatorio.")

        ciudadano = Ciudadano.objects.filter(tipo_documento=td, documento=doc).first()

        created = False
        if ciudadano is None:
            # Crear con transacción y retry ante carrera
            try:
                with transaction.atomic():
                    ciudadano = Ciudadano.objects.create(
                        tipo_documento=td,
                        documento=doc,
                        nombre=nom,
                        apellido=ape,
                        fecha_nacimiento=fecha_nac,
                        sexo=sx,
                        nacionalidad=nac,
                        provincia=prov,
                        municipio=mun,
                        localidad=loc,
                        calle=calle,
                        altura=altura,
                        codigo_postal=codigo_postal,
                        telefono=telefono,
                        email=email,
                    )
                created = True
                logger.info("Ciudadano creado: %s", ciudadano.pk)
                CiudadanoService._inicializar_dimensiones(ciudadano)
            except IntegrityError as e:
                # Si alguien lo creó entre el filter y el create, lo recuperamos
                ciudadano = Ciudadano.objects.filter(
                    tipo_documento=td, documento=doc
                ).first()
                if ciudadano is None:
                    raise ValidationError(f"No se pudo crear el ciudadano: {e}")
        else:
            # Completar sólo campos faltantes (no sobreescribir datos existentes)
            updates = []
            if not ciudadano.sexo_id and sx:
                ciudadano.sexo = sx
                updates.append("sexo")
            if not ciudadano.nombre and nom:
                ciudadano.nombre = nom
                updates.append("nombre")
            if not ciudadano.apellido and ape:
                ciudadano.apellido = ape
                updates.append("apellido")
            if not ciudadano.fecha_nacimiento and fecha_nac:
                ciudadano.fecha_nacimiento = fecha_nac
                updates.append("fecha_nacimiento")
            if not ciudadano.nacionalidad_id and nac:
                ciudadano.nacionalidad = nac
                updates.append("nacionalidad")
            if not ciudadano.provincia_id and prov:
                ciudadano.provincia = prov
                updates.append("provincia")
            if not ciudadano.municipio_id and mun:
                ciudadano.municipio = mun
                updates.append("municipio")
            if not ciudadano.localidad_id and loc:
                ciudadano.localidad = loc
                updates.append("localidad")
            if not ciudadano.calle and calle:
                ciudadano.calle = calle
                updates.append("calle")
            if ciudadano.altura is None and altura not in (None, ""):
                ciudadano.altura = altura
                updates.append("altura")
            if ciudadano.codigo_postal is None and codigo_postal not in (None, ""):
                ciudadano.codigo_postal = codigo_postal
                updates.append("codigo_postal")
            if not ciudadano.telefono and telefono:
                ciudadano.telefono = telefono
                updates.append("telefono")
            if not ciudadano.email and email:
                ciudadano.email = email
                updates.append("email")
            if updates:
                ciudadano.save(update_fields=updates)
            logger.debug("Ciudadano existente: %s", ciudadano.pk)

        # 10) Asignación de programa condicionada a la existencia del legajo
        User = get_user_model()
        if isinstance(usuario, User):
            if expediente is not None:
                existe_legajo = (
                    ExpedienteCiudadano.objects.filter(
                        expediente=expediente, ciudadano=ciudadano
                    )
                    .only("id")
                    .exists()
                )

                if existe_legajo:
                    try:
                        CiudadanoService.asignar_programa(
                            ciudadano=ciudadano,
                            usuario=usuario,
                            programa_id=programa_id,
                        )
                        logger.debug(
                            "Programa %s asegurado para ciudadano %s (con legajo existente).",
                            programa_id,
                            ciudadano.pk,
                        )
                    except Exception as e:
                        logger.warning(
                            "No se pudo asegurar programa para ciudadano %s: %s",
                            ciudadano.pk,
                            e,
                        )
                else:
                    logger.debug(
                        "No se asigna programa: no existe legajo para expediente/ciudadano (%s).",
                        ciudadano.pk,
                    )
            else:
                try:
                    CiudadanoService.asignar_programa(
                        ciudadano=ciudadano,
                        usuario=usuario,
                        programa_id=programa_id,
                    )
                    logger.debug(
                        "Programa %s asignado al ciudadano %s (sin validar legajo por no pasar expediente).",
                        programa_id,
                        ciudadano.pk,
                    )
                except Exception as e:
                    logger.warning(
                        "No se pudo asignar programa al ciudadano %s: %s",
                        ciudadano.pk,
                        e,
                    )

        return ciudadano

    @staticmethod
    def _inicializar_dimensiones(ciudadano: Ciudadano):
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        logger.info("Dimensiones inicializadas para ciudadano %s", ciudadano.pk)

    @staticmethod
    def asignar_programa(ciudadano, usuario, programa_id=1):
        _, created = CiudadanoPrograma.objects.get_or_create(
            ciudadano=ciudadano,
            programas_id=programa_id,
            defaults={"creado_por": usuario},
        )
        if created:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=programa_id,
                ciudadano=ciudadano,
                accion="agregado",
                usuario=usuario,
            )
