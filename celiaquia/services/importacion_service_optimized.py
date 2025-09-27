import logging
from functools import lru_cache
from io import BytesIO
import re

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import Q

from ciudadanos.models import Ciudadano, TipoDocumento, Sexo, Nacionalidad
from core.models import Provincia, Municipio, Localidad
from celiaquia.models import EstadoCupo, EstadoLegajo, ExpedienteCiudadano

logger = logging.getLogger(__name__)


def _norm_col(col: str) -> str:
    s = str(col).strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "columna"


@lru_cache(maxsize=1)
def _estado_doc_pendiente_id():
    try:
        return EstadoLegajo.objects.only("id").get(nombre="DOCUMENTO_PENDIENTE").id
    except EstadoLegajo.DoesNotExist:
        raise ValidationError("Falta el estado DOCUMENTO_PENDIENTE")


@lru_cache(maxsize=1)
def _tipo_doc_por_defecto():
    try:
        return TipoDocumento.objects.only("id").get(tipo__iexact="DNI").id
    except TipoDocumento.DoesNotExist:
        raise ValidationError("Falta el TipoDocumento por defecto (DNI)")


@lru_cache(maxsize=1)
def _tipo_doc_cuit():
    try:
        return TipoDocumento.objects.only("id").get(tipo__iexact="CUIT").id
    except TipoDocumento.DoesNotExist as exc:
        raise ValidationError("Falta configurar el TipoDocumento CUIT") from exc


# Estados de expediente considerados "abiertos / pre-cupo" para evitar duplicados inter-expedientes
ESTADOS_PRE_CUPO = [
    "CREADO",
    "PROCESADO",
    "EN_ESPERA",
    "CONFIRMACION_DE_ENVIO",
    "RECEPCIONADO",
    "ASIGNADO",
    "PROCESO_DE_CRUCE",
]


class ImportacionServiceOptimized:
    @staticmethod
    @transaction.atomic
    def importar_legajos_desde_excel_optimized(
        expediente, archivo_excel, usuario, batch_size=1000
    ):
        """Versión optimizada para procesar legajos masivamente.
        
        Mejoras implementadas:
        - Precarga de todos los datos necesarios en memoria
        - Bulk operations para ciudadanos y legajos
        - Cache de FKs para evitar consultas repetidas
        - Procesamiento por lotes más eficiente
        - Reducción de transacciones individuales
        """

        from celiaquia.services.ciudadano_service import CiudadanoService

        try:
            archivo_excel.open()
        except Exception:
            pass
        archivo_excel.seek(0)
        data = archivo_excel.read()

        try:
            df = pd.read_excel(BytesIO(data), engine="openpyxl", dtype=str)
        except Exception as e:
            raise ValidationError(f"No se pudo leer Excel: {e}")

        df.columns = [_norm_col(col) for col in df.columns]

        column_map = {
            "apellido": "apellido",
            "apellidos": "apellido",
            "nombre": "nombre",
            "nombres": "nombre",
            "documento": "documento",
            "numerodoc": "documento",
            "numero_documento": "documento",
            "dni": "documento",
            "fecha_nacimiento": "fecha_nacimiento",
            "fecha_de_nacimiento": "fecha_nacimiento",
            "sexo": "sexo",
            "nacionalidad": "nacionalidad",
            "municipio": "municipio",
            "localidad": "localidad",
            "email": "email",
            "telefono": "telefono",
            "codigo_postal": "codigo_postal",
            "calle": "calle",
            "altura": "altura",
        }

        present = [c for c in df.columns if c in column_map]
        df = df[present].rename(columns={c: column_map[c] for c in present}).fillna("")
        if "fecha_nacimiento" in df.columns:
            df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(
                lambda x: x.date() if hasattr(x, "date") else x
            )

        _tipo_doc_por_defecto()
        estado_id = _estado_doc_pendiente_id()
        tipo_doc_cuit_id = _tipo_doc_cuit()
        
        # Obtener provincia del usuario una sola vez
        provincia_usuario_id = None
        try:
            if hasattr(usuario, "profile") and usuario.profile.provincia_id:
                provincia_usuario_id = usuario.profile.provincia_id
        except Exception:
            pass

        validos = errores = 0
        detalles_errores = []
        excluidos = []
        warnings = []
        
        # Precarga de datos para optimizar consultas
        existentes_ids = set(
            ExpedienteCiudadano.objects.filter(expediente=expediente).values_list(
                "ciudadano_id", flat=True
            )
        )

        # Precarga de conflictos en una sola consulta optimizada
        conflictos_qs = (
            ExpedienteCiudadano.objects.select_related(
                "expediente", "expediente__estado"
            )
            .exclude(expediente=expediente)
            .filter(
                Q(estado_cupo=EstadoCupo.DENTRO)
                | Q(expediente__estado__nombre__in=ESTADOS_PRE_CUPO)
            )
            .values(
                "ciudadano_id", "estado_cupo", "es_titular_activo", 
                "expediente_id", "expediente__estado__nombre"
            )
        )

        en_programa = {}
        abiertos = {}
        for ec in conflictos_qs:
            cid = ec["ciudadano_id"]
            if ec["estado_cupo"] == EstadoCupo.DENTRO:
                en_programa[cid] = ec
            else:
                abiertos[cid] = ec

        # Precarga de todos los FKs necesarios en memoria
        fk_cache = {
            "sexo": {s.sexo.lower(): s.id for s in Sexo.objects.all()},
            "nacionalidad": {n.nacionalidad.lower(): n.id for n in Nacionalidad.objects.all()},
        }
        
        # Precarga de municipios y localidades por ID (como en el método estándar)
        municipio_ids = set()
        localidad_ids = set()
        for _, row in df.iterrows():
            if row.get('municipio'):
                mun_str = str(row['municipio']).strip()
                if mun_str and mun_str != 'nan' and mun_str.replace('.0', '').isdigit():
                    municipio_ids.add(int(float(mun_str)))
            if row.get('localidad'):
                loc_str = str(row['localidad']).strip()
                if loc_str and loc_str != 'nan' and loc_str.replace('.0', '').isdigit():
                    localidad_ids.add(int(float(loc_str)))
        
        municipios_cache = {}
        localidades_cache = {}
        if municipio_ids:
            for m in Municipio.objects.filter(pk__in=municipio_ids, provincia_id=provincia_usuario_id):
                municipios_cache[m.pk] = m.pk
        if localidad_ids:
            for l in Localidad.objects.filter(pk__in=localidad_ids):
                localidades_cache[l.pk] = l.pk
        
        # Precarga de ciudadanos existentes por documento
        documentos_excel = []
        for _, row in df.iterrows():
            doc = str(row.get('documento', '')).strip()
            if doc and doc.isdigit():
                documentos_excel.append(doc)
        
        ciudadanos_existentes = {}
        if documentos_excel:
            try:
                for c in Ciudadano.objects.filter(
                    tipo_documento_id=tipo_doc_cuit_id,
                    documento__in=documentos_excel
                ).select_related('tipo_documento', 'sexo', 'nacionalidad', 'provincia', 'municipio', 'localidad'):
                    ciudadanos_existentes[c.documento] = c
            except Exception as e:
                logger.warning("Error al precargar ciudadanos existentes: %s", e)

        numeric_fields = {
            "documento", "altura", "telefono", "telefono_alternativo", "codigo_postal"
        }

        def add_warning(fila, campo, detalle):
            warnings.append({"fila": fila, "campo": campo, "detalle": detalle})
            logger.warning("Fila %s: %s (%s)", fila, detalle, campo)

        def resolve_fk_cached(field, value):
            if not value:
                return None
            key = str(value).strip().lower()
            return fk_cache.get(field, {}).get(key)

        # Lotes para procesamiento bulk
        ciudadanos_batch = []
        legajos_batch = []
        
        # Procesar todas las filas y preparar lotes
        for offset, row in enumerate(df.to_dict(orient="records"), start=2):
            try:
                payload = {}
                for field, value in row.items():
                    v = str(value).strip()
                    if field in numeric_fields:
                        cleaned = re.sub(r"\D", "", v)
                        if cleaned:
                            payload[field] = cleaned
                        else:
                            payload[field] = None
                            if v:
                                add_warning(offset, field, "valor numérico vacío")
                    else:
                        payload[field] = v or None

                # Validaciones básicas
                required = ["apellido", "nombre", "documento", "fecha_nacimiento"]
                for req in required:
                    if not payload.get(req):
                        raise ValidationError(f"Campo obligatorio faltante: {req}")

                doc = payload.get("documento")
                if not str(doc).isdigit():
                    raise ValidationError("Documento debe contener sólo dígitos")
                
                # Normalizar fecha
                try:
                    payload["fecha_nacimiento"] = CiudadanoService._to_date(
                        payload.get("fecha_nacimiento")
                    )
                except ValidationError as e:
                    raise ValidationError(str(e))

                # Resolver FKs usando cache
                payload["tipo_documento"] = tipo_doc_cuit_id
                payload["provincia"] = provincia_usuario_id
                
                # Resolver sexo y nacionalidad por nombre
                for fk in ["sexo", "nacionalidad"]:
                    val = payload.get(fk)
                    if val:
                        resolved = resolve_fk_cached(fk, val)
                        if resolved is None:
                            add_warning(offset, fk, f"{val} no encontrado")
                            payload[fk] = None
                        else:
                            payload[fk] = resolved
                
                # Resolver municipio y localidad por ID (como en método estándar)
                municipio_val = payload.get("municipio")
                if municipio_val:
                    municipio_str = str(municipio_val).strip()
                    if municipio_str and municipio_str != 'nan' and municipio_str.replace('.0', '').isdigit():
                        municipio_id = int(float(municipio_str))
                        if municipio_id in municipios_cache:
                            payload["municipio"] = municipios_cache[municipio_id]
                        else:
                            add_warning(offset, "municipio", f"{municipio_id} no encontrado")
                            payload["municipio"] = None
                    else:
                        payload["municipio"] = None
                else:
                    payload["municipio"] = None
                
                localidad_val = payload.get("localidad")
                if localidad_val:
                    localidad_str = str(localidad_val).strip()
                    if localidad_str and localidad_str != 'nan' and localidad_str.replace('.0', '').isdigit():
                        localidad_id = int(float(localidad_str))
                        if localidad_id in localidades_cache:
                            payload["localidad"] = localidades_cache[localidad_id]
                        else:
                            add_warning(offset, "localidad", f"{localidad_id} no encontrado")
                            payload["localidad"] = None
                    else:
                        payload["localidad"] = None
                else:
                    payload["localidad"] = None

                # Validar email
                email = payload.get("email")
                if email:
                    try:
                        EmailValidator()(email)
                    except ValidationError:
                        add_warning(offset, "email", f"Email inválido: {email}")
                        payload.pop("email", None)

                # Buscar o preparar ciudadano
                ciudadano = ciudadanos_existentes.get(doc)
                if not ciudadano:
                    # Preparar para bulk_create
                    ciudadano_data = {
                        'tipo_documento_id': tipo_doc_cuit_id,
                        'documento': doc,
                        'nombre': payload.get('nombre'),
                        'apellido': payload.get('apellido'),
                        'fecha_nacimiento': payload.get('fecha_nacimiento'),
                        'sexo_id': payload.get('sexo'),
                        'nacionalidad_id': payload.get('nacionalidad'),
                        'provincia_id': payload.get('provincia'),
                        'municipio_id': payload.get('municipio'),
                        'localidad_id': payload.get('localidad'),
                        'calle': payload.get('calle'),
                        'altura': payload.get('altura'),
                        'codigo_postal': payload.get('codigo_postal'),
                        'telefono': payload.get('telefono'),
                        'email': payload.get('email'),
                    }
                    # Validar datos antes de agregar al batch
                    if ciudadano_data['nombre'] and ciudadano_data['apellido']:
                        ciudadanos_batch.append((doc, ciudadano_data, offset))
                    else:
                        raise ValidationError("Nombre y apellido son obligatorios")
                else:
                    # Verificar exclusiones para ciudadano existente
                    cid = ciudadano.pk
                    
                    if cid in existentes_ids:
                        excluidos.append({
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": doc,
                            "nombre": payload.get('nombre', ''),
                            "apellido": payload.get('apellido', ''),
                            "motivo": "Ya existe en este expediente",
                        })
                        continue

                    if cid in en_programa:
                        prog = en_programa[cid]
                        estado_text = "ACEPTADO" if prog["es_titular_activo"] else "SUSPENDIDO"
                        excluidos.append({
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": doc,
                            "nombre": payload.get('nombre', ''),
                            "apellido": payload.get('apellido', ''),
                            "expediente_origen_id": prog["expediente_id"],
                            "estado_programa": estado_text,
                            "motivo": "Ya está dentro del programa en otro expediente",
                        })
                        continue

                    if cid in abiertos:
                        conflict = abiertos[cid]
                        excluidos.append({
                            "fila": offset,
                            "ciudadano_id": cid,
                            "documento": doc,
                            "nombre": payload.get('nombre', ''),
                            "apellido": payload.get('apellido', ''),
                            "expediente_origen_id": conflict["expediente_id"],
                            "estado_expediente_origen": conflict["expediente__estado__nombre"],
                            "motivo": "Duplicado en otro expediente abierto",
                        })
                        continue
                    
                    # OK para crear legajo
                    legajos_batch.append((ciudadano, offset))
                    existentes_ids.add(cid)
                    validos += 1

            except Exception as e:
                errores += 1
                detalles_errores.append({"fila": offset, "error": str(e)})
                logger.error("Error fila %s: %s", offset, e)

        # Procesar ciudadanos nuevos en lotes
        if ciudadanos_batch:
            nuevos_ciudadanos = []
            for doc, data, offset in ciudadanos_batch:
                try:
                    ciudadano = Ciudadano(**data)
                    nuevos_ciudadanos.append(ciudadano)
                    legajos_batch.append((ciudadano, offset))
                    validos += 1
                except Exception as e:
                    errores += 1
                    detalles_errores.append({"fila": offset, "error": str(e)})
            
            # Bulk create de ciudadanos nuevos
            if nuevos_ciudadanos:
                try:
                    created_ciudadanos = Ciudadano.objects.bulk_create(
                        nuevos_ciudadanos, batch_size=batch_size, ignore_conflicts=True
                    )
                    logger.info("Creados %s ciudadanos nuevos", len(created_ciudadanos))
                    
                    # Recargar ciudadanos creados para obtener sus IDs
                    docs_nuevos = [c.documento for c in nuevos_ciudadanos]
                    if docs_nuevos:
                        ciudadanos_creados = {c.documento: c for c in Ciudadano.objects.filter(
                            tipo_documento_id=tipo_doc_cuit_id, documento__in=docs_nuevos
                        )}
                        
                        # Actualizar referencias en legajos_batch
                        legajos_batch_actualizado = []
                        for ciudadano, offset in legajos_batch:
                            if not hasattr(ciudadano, 'pk') or not ciudadano.pk:
                                ciudadano_actualizado = ciudadanos_creados.get(ciudadano.documento)
                                if ciudadano_actualizado:
                                    ciudadano = ciudadano_actualizado
                            legajos_batch_actualizado.append((ciudadano, offset))
                        legajos_batch = legajos_batch_actualizado
                    
                except Exception as e:
                    logger.error("Error en bulk_create de ciudadanos: %s", e)
                    # Fallback: crear ciudadanos uno por uno
                    for ciudadano in nuevos_ciudadanos:
                        try:
                            ciudadano.save()
                        except Exception as save_error:
                            logger.error("Error al crear ciudadano %s: %s", ciudadano.documento, save_error)

        # Bulk create de legajos
        if legajos_batch:
            legajos_crear = []
            for ciudadano, offset in legajos_batch:
                if hasattr(ciudadano, 'pk') and ciudadano.pk:
                    legajos_crear.append(ExpedienteCiudadano(
                        expediente=expediente,
                        ciudadano=ciudadano,
                        estado_id=estado_id,
                    ))
                else:
                    logger.warning("Ciudadano sin PK en fila %s, saltando", offset)
            
            if legajos_crear:
                try:
                    created_legajos = ExpedienteCiudadano.objects.bulk_create(
                        legajos_crear, batch_size=batch_size, ignore_conflicts=True
                    )
                    logger.info("Creados %s legajos", len(created_legajos))
                except Exception as e:
                    logger.error("Error en bulk_create de legajos: %s", e)
                    # Fallback: crear legajos uno por uno
                    for legajo in legajos_crear:
                        try:
                            legajo.save()
                        except Exception as save_error:
                            logger.error("Error al crear legajo para ciudadano %s: %s", 
                                       legajo.ciudadano.documento, save_error)
                            errores += 1
                            validos -= 1

        logger.info(
            "Import optimizado completo: %s válidos, %s errores, %s excluidos.",
            validos, errores, len(excluidos)
        )

        return {
            "validos": validos,
            "errores": errores,
            "detalles_errores": detalles_errores,
            "excluidos_count": len(excluidos),
            "excluidos": excluidos,
            "warnings": warnings,
        }