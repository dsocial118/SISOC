# Documento funcional - Navegación por Sector > Subsector > Cursos (API VAT Web)

Fecha: 2026-04-01

## Objetivo

Definir el flujo funcional para una experiencia en 3 pantallas:

1. Primera pantalla: listado por Sector.
2. Segunda pantalla: listado por Subsector (según sector elegido).
3. Tercera pantalla: cards con todos los cursos filtrados por ese Subsector.

Este documento está enfocado en navegación y consumo de APIs para cursos.

## Base URL y autenticación

Base:

- /api/vat/web/

Autenticación:

- API key válida o
- token de usuario autenticado

Permiso aplicado: HasAPIKeyOrToken.

## Endpoints a consumir

### 1) Sectores/Subsectores (fuente para pantalla 1 y 2)

Endpoint:

- GET /api/vat/web/titulos/

Uso funcional:

- Extraer sectores únicos para la pantalla 1.
- Extraer subsectores únicos del sector elegido para la pantalla 2.

Filtros disponibles:

- q
- sector_id
- subsector_id
- activo

### 2) Cursos (pantalla 3)

Endpoint:

- GET /api/vat/web/cursos/

Uso funcional:

- Mostrar cards de cursos/comisiones.

Filtros disponibles:

- q
- centro_id
- titulo_id
- programa_id
- ciclo_lectivo
- estado
- usa_voucher

## Flujo funcional solicitado

### Pantalla 1 - Sectores

Objetivo:

- Mostrar todas las opciones de sector.

Consumo:

- GET /api/vat/web/titulos/?activo=true

Lógica de front:

- Agrupar por `sector` y `sector_nombre`.
- Mostrar 1 card por sector.

### Pantalla 2 - Subsectores

Objetivo:

- Al elegir un sector, mostrar solo sus subsectores.

Consumo:

- GET /api/vat/web/titulos/?activo=true&sector_id={sector_id}

Lógica de front:

- Agrupar por `subsector` y `subsector_nombre`.
- Mostrar 1 card por subsector.

### Pantalla 3 - Cursos

Objetivo:

- Al elegir un subsector, mostrar todos los cursos relacionados.

Consumo recomendado:

1. GET /api/vat/web/titulos/?activo=true&sector_id={sector_id}&subsector_id={subsector_id}
2. Con los `id` de títulos obtenidos, consultar cursos por `titulo_id`.

Ejemplo de llamadas:

- GET /api/vat/web/cursos/?titulo_id=52
- GET /api/vat/web/cursos/?titulo_id=53

Nota funcional importante:

- El endpoint de cursos no expone hoy `sector_id` ni `subsector_id` como query params directos.
- Por eso el filtro por subsector se resuelve a través de `titulo_id`.

## Ejemplos de requests

- GET /api/vat/web/titulos/?activo=true
- GET /api/vat/web/titulos/?activo=true&sector_id=3
- GET /api/vat/web/titulos/?activo=true&sector_id=3&subsector_id=11
- GET /api/vat/web/cursos/?titulo_id=52
- GET /api/vat/web/cursos/?titulo_id=52&estado=activa
- GET /api/vat/web/cursos/?titulo_id=52&usa_voucher=false

## Ejemplo de respuesta JSON - Pantalla 1/2 (Títulos con sector/subsector)

[
  {
    "id": 52,
    "nombre": "Operador en Soldadura",
    "codigo_referencia": "SOL-001",
    "descripcion": "Trayecto inicial de soldadura",
    "activo": true,
    "plan_estudio": 14,
    "sector": 3,
    "sector_nombre": "Industria",
    "subsector": 11,
    "subsector_nombre": "Metalmecánica"
  }
]

## Ejemplo de respuesta JSON - Pantalla 3 (Cursos)

[
  {
    "id": 3,
    "codigo_comision": "CUR-2026-03",
    "nombre": "Soldadura Inicial - Comisión A",
    "estado": "activa",
    "estado_oferta": "publicada",
    "fecha_inicio": "2026-04-10",
    "fecha_fin": "2026-08-30",
    "cupo": 30,
    "total_inscriptos": 12,
    "cupos_disponibles": 18,
    "centro_id": 10,
    "centro_nombre": "CFP 777",
    "titulo_id": 52,
    "titulo_nombre": "Operador en Soldadura",
    "plan_curricular_id": 14,
    "plan_curricular_nombre": "Plan Soldadura 2026",
    "programa_id": 6,
    "programa_nombre": "Formación Laboral",
    "ciclo_lectivo": 2026,
    "costo": "0.00",
    "usa_voucher": false,
    "observaciones": "Comisión presencial turno tarde",
    "horarios": [
      {
        "id": 101,
        "dia_semana": 2,
        "dia_nombre": "Martes",
        "hora_desde": "18:00:00",
        "hora_hasta": "21:00:00",
        "aula_espacio": "Taller 1"
      },
      {
        "id": 102,
        "dia_semana": 4,
        "dia_nombre": "Jueves",
        "hora_desde": "18:00:00",
        "hora_hasta": "21:00:00",
        "aula_espacio": "Taller 1"
      }
    ]
  }
]

## Swagger VAT

- /api/docs/VAT/
- /api/schema/VAT/
- /api/redoc/VAT/

## Resumen

Para el flujo pedido (Sector > Subsector > Cursos), los endpoints mínimos son:

1. GET /api/vat/web/titulos/
2. GET /api/vat/web/cursos/

Regla de implementación:

- Sector y Subsector se resuelven desde `titulos`.
- Cursos se listan filtrando por `titulo_id`.
