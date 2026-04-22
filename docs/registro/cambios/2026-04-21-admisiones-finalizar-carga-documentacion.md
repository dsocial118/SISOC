# 2026-04-21 - Admisiones: estado intermedio para finalizar carga documental

## Cambio
Se agregó un estado intermedio en admisiones técnicas para separar:
- documentación aprobada por abogado,
- decisión final del técnico de cerrar la etapa documental.

Nuevo estado de admisión:
- `documentacion_carga_finalizada` ("Carga de documentación finalizada").

## Comportamiento nuevo
1. El abogado sigue aprobando/rectificando documentos como hasta ahora.
2. Cuando todo obligatorio queda aprobado, la admisión queda en `documentacion_aprobada`.
3. En ese estado, el técnico ve el botón `Finalizar carga documentación`.
4. Al confirmar, la admisión pasa a `documentacion_carga_finalizada`.
5. Recién en ese estado aparece el botón `Caratular expediente`.

## Validaciones
- Se agregó control de backend para bloquear caratulación si no se finalizó antes la carga documental.
- Si un documento pasa a `Rectificar`, también se contempla el nuevo estado en el rollback a `documentacion_en_proceso`.

## Alcance
- Servicios de admisiones técnicas (`AdmisionService`).
- Template de edición técnica (modal nuevo).
- Templatetags de botones y formateo de estados.
- Choices del modelo `Admision` + migración.
- Tests unitarios/caracterización ajustados.
