# Ajustes de modificación documental técnica e impacto IF/GDE

## Fecha
2026-04-21

## Objetivo
Permitir que técnicos modifiquen documentación (incluso validada) hasta la etapa final del informe técnico, y bloquear esas modificaciones cuando el informe técnico ya no esté iniciado ni en borrador. Asegurar además que cualquier modificación documental invalide IF/GDE para forzar recomposición del informe técnico.

## Alcance
Se incluyeron reglas backend para subir/reemplazar, crear personalizado, eliminar, cambiar estado de documento y editar número GDE; más un ajuste mínimo de UI para exponer eliminación en documentos validados con control final en backend.

## Archivos tocados
- admisiones/services/admisiones_service/impl.py
- admisiones/views/web_views.py
- admisiones/templates/admisiones/includes/documento_row.html

## Cambios realizados
- Se agregó validación centralizada para bloquear modificaciones documentales por técnico cuando el último informe técnico `base` ya no está en estado `Iniciado` ni con formulario `borrador`.
- Se aplicó esa validación en altas/reemplazos de archivo, creación de documento personalizado, eliminación, cambio de estado de documento y edición de número GDE.
- Se agregó limpieza de IF/GDE de admisión ante cambios documentales (reseteo de `numero_if_tecnico`, `archivo_informe_tecnico_GDE` y rollback de estado desde `if_informe_tecnico_cargado` a `informe_tecnico_aprobado` cuando corresponde).
- Cuando una modificación documental deja de cumplir la etapa vigente, la admisión vuelve al estado documental consistente (`documentacion_en_proceso`, `documentacion_finalizada` o `documentacion_aprobada` según corresponda).
- Se habilitó visualmente el botón `Eliminar` también en documentos validados; el permiso efectivo queda controlado por backend y etapa del informe.

## Supuestos
- La restricción de bloqueo aplica específicamente a técnicos de dupla; superuser y perfiles no técnicos mantienen capacidad de gestión para soporte/operación.
- El impacto solicitado sobre IF/GDE se modela como invalidación y recarga posterior.

## Validaciones ejecutadas
- `python -m compileall` sobre archivos modificados para verificar sintaxis.

## Pendientes / riesgos
- La regresión quedó cubierta con tests unitarios enfocados sobre recálculo documental y selección del informe técnico `base`.
- El branch contiene cambios previos relacionados al flujo documental (estado intermedio de finalización), documentados por separado.
