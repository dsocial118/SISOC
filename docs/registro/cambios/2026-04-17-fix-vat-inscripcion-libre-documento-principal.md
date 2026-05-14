# Fix VAT Web - documento principal en inscripcion libre

Fecha: 2026-04-17

## Que cambio

- En `VAT/serializers.py`, la alta web de inscripciones libres ahora completa `datos_postulante.documento` con el `documento` principal del request cuando ese DNI ya vino informado y el objeto del postulante no lo trae.
- Se agrego un test de regresion en `VAT/tests.py` con el payload reportado por la integracion externa.

## Problema resuelto

En cursos con `inscripcion_libre=true`, si la API recibia:

- `documento` en el nivel principal, y
- `datos_postulante` sin `documento` pero con `cuil`,

la creacion automatica del ciudadano terminaba guardando el CUIL como documento. Eso rompia la trazabilidad del flujo esperado por Mi Argentina/VAT, porque luego `GET /api/vat/web/inscripciones/?documento=<dni>` no recuperaba la inscripcion creada con el DNI original.

## Decision

Se prioriza el `documento` principal del request como fuente de verdad para la identidad del ciudadano cuando el postulante no repite ese dato dentro de `datos_postulante`.

El fallback al CUIL se mantiene solo para los casos donde realmente no llega ningun documento explicito.

## Validacion

- `docker compose exec -T django pytest VAT/tests.py -k "prioriza_documento_principal_sobre_cuil" -q`
- `docker compose exec -T django pytest VAT/tests.py -k "mi_argentina_flujo_completo_prevalidar_e_inscribir or inscripcion_libre_crea_inscripcion_operativa_sin_ciudadano or inscripcion_libre_usa_cuil_como_documento_si_no_viene_documento or prioriza_documento_principal_sobre_cuil" -q`
- `docker compose exec -T django black VAT/serializers.py VAT/tests.py --check --config pyproject.toml`
