# API web de VAT

Fecha: 2026-03-25

## Objetivo

Exponer endpoints orientados a consumo de frontend para:

- listar centros,
- listar títulos,
- listar cursos/comisiones,
- crear y consultar inscripciones de ciudadanos.

## Autenticación

Los endpoints usan `HasAPIKeyOrToken`, por lo que aceptan:

- API key válida,
- usuario autenticado por token.

## Endpoints

Base: `/api/vat/web/`

### `GET /centros/`

Devuelve centros visibles para la web.

Filtros:

- `q`
- `provincia_id`
- `municipio_id`
- `localidad_id`
- `activo`

### `GET /titulos/`

Devuelve títulos de referencia para navegación y filtros del frontend.

Filtros:

- `q`
- `sector_id`
- `subsector_id`
- `activo`

### `GET /cursos/`

Devuelve cursos/comisiones con:

- centro,
- título,
- plan curricular,
- programa,
- costo,
- uso de voucher,
- cupo total,
- cupos disponibles,
- horarios.

Filtros:

- `q`
- `centro_id`
- `titulo_id`
- `programa_id`
- `ciclo_lectivo`
- `estado`
- `usa_voucher`

### `GET /inscripciones/`

Consulta inscripciones existentes.

Filtros:

- `ciudadano_id`
- `documento`
- `estado`

### `GET /ciudadanos/voucher-estado/`

Consulta el estado general del voucher de un ciudadano por DNI, sin requerir una comision concreta.

Query:

- `documento`: DNI numerico del ciudadano.

Respuesta funcional:

- `Disponible`: tiene voucher usable y no tiene inscripciones VAT activas.
- `En uso`: tiene voucher usable y tiene alguna inscripcion VAT activa.
- `No disponible`: no existe ciudadano para el DNI o no tiene voucher usable.

Se considera voucher usable a un voucher `activo`, no vencido y con saldo disponible.
Se consideran inscripciones activas los estados `pre_inscripta`, `en_espera`, `inscripta`
y `validada_presencial`.

Ejemplo:

```json
{
  "documento": "30111222",
  "estado": "Disponible",
  "tiene_voucher": true,
  "esta_inscripto": false
}
```

### `POST /inscripciones/`

Crea una inscripción VAT y, si la oferta usa voucher, descuenta el costo configurado.

Cuando la inscripción pública crea un ciudadano en forma automática, `datos_postulante.telefono`
admite formatos internacionales y cadenas de hasta 50 caracteres, por ejemplo con prefijo `+54`,
separadores o interno.

### `POST /inscripciones/prevalidar/`

Prevalida si una persona puede inscribirse antes de confirmar el alta.

Valida:

- existencia del ciudadano,
- existencia de la comisión de curso,
- estado del curso y de la comisión,
- cupos disponibles,
- inscripción duplicada,
- voucher activo, saldo y parametría habilitada cuando el curso usa voucher,
- regla de inscripción única activa si aplica.

Respuesta funcional:

- `puede_inscribirse`,
- `motivos`,
- resumen del ciudadano,
- resumen de la comisión,
- estado del voucher y saldo post inscripción estimado.

Payloads admitidos:

```json
{
  "ciudadano_id": 1,
  "comision_id": 3,
  "estado": "inscripta",
  "observaciones": "Alta desde la web"
}
```

```json
{
  "documento": "30111222",
  "comision_id": 3,
  "estado": "pre_inscripta"
}
```

## Documentación Swagger

Los endpoints quedan documentados en `/api/docs/` bajo los tags:

- `VAT Web - Centros`
- `VAT Web - Ciudadanos`
- `VAT Web - Títulos`
- `VAT Web - Cursos`
- `VAT Web - Inscripciones`

También queda disponible una entrada directa para VAT, filtrada para mostrar solo endpoints `/api/vat/`:

- Swagger VAT: `/api/docs/VAT/`
- Schema VAT: `/api/schema/VAT/`
- ReDoc VAT: `/api/redoc/VAT/`
