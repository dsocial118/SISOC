# Decisión: Modelo de identidad en Ciudadano

**Fecha:** 2026-04-10



---

## Contexto

El modelo `Ciudadano` solo admitía registros con DNI único y datos completos. Hay tres
casos reales que el sistema no podía manejar:

1. **Estándar**: DNI presente y RENAPER confirma los datos.
2. **Sin DNI**: la persona no tiene número de documento (no DNI físico ausente, sino
   número inexistente). Se espera que genere duplicados — aceptado como condición operativa.
3. **DNI no validado por RENAPER**: el DNI existe pero los datos de RENAPER no coinciden.

---

## Decisión

Mantener un **único modelo `Ciudadano`** con campos adicionales de identidad.
No crear modelos paralelos.

### Cambio de unicidad

- Se **elimina** `unique_together("tipo_documento", "documento")`.
- Se agrega `documento_unico_key` (CharField, nullable, unique).
  - Solo se completa en registros `ESTANDAR` con DNI único verificado.
  - `NULL` en `SIN_DNI` y `DNI_NO_VALIDADO_RENAPER` para permitir duplicados
    sin romper integridad global (MySQL: NULL != NULL en índice único).

### Campos nuevos

| Campo | Tipo | Propósito |
|---|---|---|
| `tipo_registro_identidad` | CharField (enum) | ESTANDAR / SIN_DNI / DNI_NO_VALIDADO_RENAPER |
| `estado_validacion_renaper` | CharField (enum) | NO_CONSULTADO / VALIDADO / NO_VALIDADO |
| `fecha_validacion_renaper` | DateTimeField | Cuándo se consultó RENAPER |
| `datos_renaper` | JSONField | Respuesta cruda de RENAPER |
| `motivo_sin_dni` | CharField (enum) | Por qué no tiene DNI |
| `motivo_sin_dni_descripcion` | TextField | Detalle libre |
| `motivo_no_validacion_renaper` | CharField (enum) | Por qué RENAPER no validó |
| `motivo_no_validacion_descripcion` | TextField | Detalle libre |
| `requiere_revision_manual` | BooleanField | True en SIN_DNI y DNI_NO_VALIDADO |
| `identificador_interno` | CharField (unique, nullable) | Clave operativa generada (`CIU-<id>`) |
| `documento_unico_key` | CharField (unique, nullable) | Reemplaza unique_together |

### Enums acordados con funcionales (2026-04-09)

**Motivos sin DNI:**
- `NO_REGISTRADO_NACER` — No fue registrado al nacer
- `MENOR_SIN_DOCUMENTO` — Menor de edad sin documento tramitado
- `EXTRANJERO_SIN_DNI` — Extranjero sin DNI argentino
- `DOCUMENTO_EXTRAVIADO` — Documento extraviado o en trámite
- `VULNERABILIDAD_EXTREMA` — Víctima de violencia / vulnerabilidad extrema
- `OTRO` — Otro (con campo de texto libre)

**Motivos DNI no validado por RENAPER:**
- `ERROR_TRANSCRIPCION` — Errores en la transcripción de datos manuales
- `RENAPER_DESACTUALIZADO` — Cambios recientes en RENAPER aún no reflejados
- `DOC_NO_ACTUALIZADA` — Documentación del usuario no actualizada
- `ERROR_TIPOGRAFICO` — Errores tipográficos en el ingreso de datos
- `MULTIPLES_IDENTIDADES` — Personas con múltiples identidades o nombres
- `CAMBIO_NOMBRE_LEGAL` — Cambios de nombre legal no registrados en RENAPER
- `DIFERENCIA_FORMATO_NOMBRE` — Diferencias en el formato o tipo de nombre
- `DISCREPANCIA_FECHA_NACIMIENTO` — Discrepancias en fechas de nacimiento o partidas
- `OTRO` — Otro (con campo de texto libre)

### Rol de revisión

Rol nuevo: `revisión_usuarios`. Lo tienen quienes ya pueden editar usuarios +
se puede asignar a revisores específicos. **Cierre de revisión → v2.**

---

## Diferido a v2

- `nivel_confianza_identidad` (int 0–100)
- `hash_identidad_aproximada` (detección automática de duplicados)
- Flujo de cierre de revisión manual

---

## Fases de implementación

| Fase | Descripción | Estado |
|---|---|---|
| **Fase 1** | Migración de schema + backfill sin cambio funcional | En progreso |
| **Fase 2** | Alta de ciudadanos SIN_DNI (form, búsqueda, nómina, badge) | Pendiente |
| **Fase 3** | Alta DNI_NO_VALIDADO_RENAPER + ajuste de `.first()` por DNI | Pendiente |
| **Fase 4** | Tests de regresión (ciudadanos, nómina, celiaquía, admisiones) | Pendiente |

---

## Backfill de datos existentes

**Problema detectado:** hay 24.926 DNIs duplicados en producción a pesar del
`unique_together`. Indica que el constraint no estaba activo a nivel DB (pendiente
confirmación con `SHOW INDEX`).

**Estrategia acordada:**
- Ciudadanos con DNI único → `ESTANDAR` + `documento_unico_key` poblado
- Ciudadanos con DNI duplicado → `DNI_NO_VALIDADO_RENAPER` + `requiere_revision_manual=True`
- Ciudadanos sin documento → `SIN_DNI` + `requiere_revision_manual=True`

**Ejecución:**
```bash
# Auditoría previa (dry-run)
python manage.py backfill_identidad --dry-run

# Solo estadísticas
python manage.py backfill_identidad --solo-estadisticas

# Ejecución real (en horario de baja carga, con backup previo)
python manage.py backfill_identidad --batch-size 500
```

**Pendiente antes de ejecutar en producción:**
- Resultado de `SHOW INDEX FROM ciudadanos_ciudadano` (infra)
- Backup de tabla `ciudadanos_ciudadano`
- Ventana de baja carga coordinada

---

## Archivos tocados (Fase 1)

- `ciudadanos/models.py` — campos nuevos + enums + eliminación de unique_together
- `ciudadanos/migrations/0023_ciudadano_identidad_fase1.py` — migración de schema
- `ciudadanos/management/commands/backfill_identidad.py` — comando de backfill
- `docs/registro/decisiones/2026-04-10-identidad-ciudadano.md` — este archivo
