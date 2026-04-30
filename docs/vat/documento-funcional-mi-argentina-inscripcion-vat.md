# Documento funcional - Flujo Mi Argentina -> VAT

Fecha: 2026-04-11

## Objetivo

Definir el flujo de integración para que una aplicación externa, como Mi Argentina, pueda consultar oferta VAT, prevalidar elegibilidad e inscribir ciudadanos sin replicar reglas de negocio fuera de SISOC.

Colección Postman de referencia:

- `postman/VAT Web - Mi Argentina Inscripcion.postman_collection.json`

## Principio de integración

- Mi Argentina autentica e identifica al usuario.
- SISOC resuelve elegibilidad, voucher, cupo y alta de inscripción.
- El frontend externo consume endpoints; no decide reglas de negocio.

## Claims esperables desde Mi Argentina

De la autenticación OAuth/OpenID se espera al menos:

- `dni_number`
- `cuil` cuando esté disponible
- `name` / `given_name` / `family_name`
- `email`
- `validation_level`

En la integración propuesta, el dato mínimo obligatorio para SISOC es el documento del ciudadano. El resto puede usarse como trazabilidad o validaciones futuras, pero no reemplaza la lógica del backend VAT.

## Flujo propuesto

### 1. Descubrir centros

- `GET /api/vat/web/centros/`

Uso:

- listar centros disponibles,
- aplicar filtros geográficos,
- obtener `centro_id`.

### 2. Listar cursos/comisiones visibles para el centro

- `GET /api/vat/web/cursos/?centro_id=<id>`

Uso:

- mostrar comisiones reales de `ComisionCurso`,
- exponer si usan voucher,
- informar programa, costo, cupo y cupos disponibles,
- capturar `comision_curso_id`.

### 3. Consultar estado general de voucher

- `GET /api/vat/web/ciudadanos/voucher-estado/?documento=<dni>`

Uso:

- mostrar si el voucher esta `Disponible`, `En uso` o `No disponible`,
- resolver un diagnostico rapido por DNI antes de elegir una comision,
- evitar que el frontend reconstruya reglas de voucher e inscripcion.

Respuesta esperable:

```json
{
  "documento": "32123456",
  "estado": "Disponible",
  "tiene_voucher": true,
  "esta_inscripto": false
}
```

Estados:

- `Disponible`: tiene voucher usable y no tiene inscripciones VAT activas.
- `En uso`: tiene voucher usable y tiene alguna inscripcion VAT activa.
- `No disponible`: no existe ciudadano para el DNI o no tiene voucher usable.

### 4. Prevalidar inscripción

- `POST /api/vat/web/inscripciones/prevalidar/`

Payload sugerido:

```json
{
  "documento": "32123456",
  "cuil": "27-32123456-4",
  "comision_curso_id": 15
}
```

Validaciones resueltas por SISOC:

- el ciudadano existe,
- la comisión existe,
- el curso está activo,
- la comisión está activa,
- la comisión tiene cupos,
- la persona no está ya inscripta,
- si usa voucher: hay voucher activo, parametría válida, saldo suficiente,
- si corresponde: se cumple la regla de inscripción única activa.

Respuesta esperable:

```json
{
  "puede_inscribirse": true,
  "motivos": [],
  "ciudadano": {
    "id": 99,
    "documento": 32123456,
    "nombre": "Andrea García"
  },
  "comision": {
    "id": 15,
    "codigo_comision": "MIARG-01",
    "nombre": "Comisión Mi Argentina",
    "estado": "activa",
    "curso_id": 10,
    "curso_nombre": "Curso Mi Argentina",
    "centro_id": 7,
    "centro_nombre": "CFP 501",
    "programa_id": 3,
    "programa_nombre": "Programa Mi Argentina",
    "usa_voucher": true,
    "cupo_total": 12,
    "cupos_disponibles": 12,
    "costo": 2
  },
  "voucher": {
    "requerido": true,
    "programa_id": 3,
    "programa_nombre": "Programa Mi Argentina",
    "parametrias_habilitadas": [4],
    "voucher_id": 22,
    "parametria_id": 4,
    "saldo_actual": 6,
    "credito_requerido": 2,
    "saldo_post_inscripcion": 4
  }
}
```

### 5. Confirmar inscripción

- `POST /api/vat/web/inscripciones/`

Payload sugerido:

```json
{
  "documento": "32123456",
  "comision_curso_id": 15,
  "estado": "inscripta",
  "observaciones": "Alta desde Mi Argentina"
}
```

Resultado:

- se crea la inscripción,
- si usa voucher se debitan créditos,
- se devuelve la inscripción con el detalle del curso/comisión.

### 6. Consultar inscripción generada

- `GET /api/vat/web/inscripciones/?documento=<dni>`

Uso:

- mostrar estado final al usuario,
- refrescar la inscripción creada,
- auditar el resultado del flujo externo.

## Contrato de responsabilidades

### Mi Argentina

- autentica al usuario,
- obtiene claims de identidad,
- consume endpoints de SISOC,
- muestra mensajes y confirmaciones al usuario final.

### SISOC

- decide elegibilidad,
- valida voucher y parametrías,
- controla cupos,
- evita duplicados,
- ejecuta el débito de voucher,
- persiste la inscripción.

## Flujo probado

Se dejó cubierto por tests automáticos en `VAT/tests.py` un recorrido completo:

1. listado de centros,
2. listado de cursos por centro,
3. prevalidación con voucher,
4. inscripción final,
5. consulta posterior de la inscripción,
6. verificación del saldo remanente del voucher.
