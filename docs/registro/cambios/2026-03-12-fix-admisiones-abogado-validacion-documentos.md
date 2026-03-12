# Fix: validación de documentos por abogado en Admisiones Técnicos

## Contexto
En la pantalla `/comedores/admisiones/tecnicos/editar/<pk>`, en la card **Documentos requeridos**, el usuario abogado de dupla debía poder pasar un documento desde **A Validar Abogado** a **Aceptado** o **Rectificar**.

## Causa raíz
En `admisiones/templates/admisiones/includes/documento_row.html` había una condición duplicada con el mismo `has_any_perm(...)` en `if`/`elif`, dejando inalcanzable el bloque que renderiza el `<select>` para el abogado cuando el estado era **A Validar Abogado**.

## Cambios aplicados
- Se corrigió el render condicional para que el `<select>` de transición de estado aparezca cuando el usuario tiene `auth.role_abogado_dupla` y existe `archivo_id`.
- Se mantiene la visualización como badge para el resto de usuarios con permisos de vista.
- Se agregó test de regresión de template:
  - abogado con `auth.role_abogado_dupla` -> ve selector con opciones `Aceptado` y `Rectificar`.
  - usuario sin rol abogado (técnico) -> ve badge, no selector.

## Permisos relevantes para este flujo
Para que un abogado pueda operar en esta pantalla y cambiar estado de documentos:
- Permisos de acceso a la vista:
  - `comedores.view_comedor`
  - `admisiones.view_admision`
  - `acompanamientos.view_informacionrelevante`
- Permiso de rol para habilitar el selector de validación de abogado:
  - `auth.role_abogado_dupla`
- Además, debe estar asignado como abogado de la dupla activa del comedor de la admisión.

## Validación
- Se agregó `admisiones/tests/test_documento_row_template.py`.
- En este entorno no fue posible correr tests en Docker (`docker` no disponible en WSL de esta sesión) ni pytest local por dependencia faltante (`sentry_sdk`).
