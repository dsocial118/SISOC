# Permisos configurables por etapa de rendiciones

Las acciones del flujo web de rendiciones mensuales dejaron de depender de
nombres de grupos hardcodeados. Se incorporaron cuatro permisos Django:

- `manage_territorial_stage`: Revisión Territorial.
- `manage_auditoria_review_stage`: Revisión de Auditoría.
- `manage_auditoria_stage`: Auditoría.
- `manage_regularizacion_stage`: Regularización.

Cada permiso habilita todas las acciones propias de su etapa, incluida la
revisión y solicitud de documentación faltante en las dos etapas de revisión.
Los botones y los POST usan la misma validación; ocultar una acción en la interfaz
no reemplaza la autorización del backend.

Los permisos de etapa también habilitan el acceso al listado, detalle y descarga
de rendiciones, además de mostrar la entrada correspondiente en el menú. No
habilitan por sí solos la edición de datos generales, creación ni eliminación.

Los permisos se pueden asignar a cualquier grupo desde el ABM de Grupos. La
migración conserva compatibilidad otorgando Revisión Territorial al grupo
homónimo, las tres etapas posteriores a `Rendición Auditoría` y las cuatro a
`Administrador Auditoría`.

## Despliegue

Ejecutar `python manage.py migrate`. Luego configurar el grupo responsable de
cada etapa desde Usuarios > Grupos y asignarle únicamente el permiso de etapa
correspondiente.

Para pruebas locales se incorporó el comando idempotente
`seed_rendicion_stage_examples`. Requiere `--comedor-id` y `--password`, crea
cuatro usuarios/grupos QA aislados y cuatro rendiciones listas para iniciar cada
etapa. No contiene credenciales predeterminadas.

Solicitar un documento faltante ya no interrumpe inmediatamente la etapa de
revisión. El equipo puede acumular solicitudes y continuar validando documentos;
al finalizar Revisión Territorial o Revisión de Auditoría, la existencia de al
menos una solicitud activa deriva la rendición a subsanación.

Las observaciones ingresadas al solicitar un documento faltante se muestran en
el detalle debajo de la categoría correspondiente, junto con una marca visible
de solicitud activa, del mismo modo que las observaciones de una subsanación.
