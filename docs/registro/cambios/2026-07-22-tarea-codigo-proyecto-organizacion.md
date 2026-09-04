# Tarea: migración del código de proyecto desde comedor hacia la organización

**Fecha:** 2026-07-22  
**Estado:** propuesta  
**Área:** comedores / organizaciones

## Contexto

Hoy el campo `codigo_de_proyecto` está en el modelo de comedor y se completa en el alta del legajo. El negocio requiere que ese dato pertenezca a la organización y que la selección del proyecto para un comedor dependa de la organización elegida.

## Objetivo

Implementar una transición ordenada desde el modelo actual hacia un modelo donde la organización tenga asociados los proyectos válidos y el comedor seleccione un proyecto compatible con esa organización.

## Propuesta recomendada

Adoptar una entidad de proyectos por organización, en lugar de solo agregar un campo único en la organización.

### Alternativa recomendada

- crear una entidad nueva para proyectos asociados a la organización;
- migrar los datos actuales desde `Comedor.codigo_de_proyecto`;
- ajustar el formulario de comedor para que muestre solo los proyectos válidos de la organización seleccionada;
- mantener compatibilidad temporal con el dato actual del comedor hasta completar la migración.

## Alcance

- definir la nueva entidad de proyectos vinculada a `Organizacion`;
- migrar datos históricos de proyecto desde los comedores;
- adaptar alta/edición de comedor para usar la nueva relación;
- ajustar serializers, vistas y reglas de negocio;
- documentar la transición para evitar inconsistencias futuras.

## Criterios de aceptación

- una organización puede tener múltiples proyectos asociados;
- un comedor solo puede seleccionar proyectos válidos para su organización;
- los datos actuales se conservan y se migran correctamente;
- el flujo de UI y backend usa la nueva relación de forma consistente.

## Nota de implementación

La transición debe hacerse de forma gradual para no romper el funcionamiento actual: el dato existente debe pasarse a la nueva estructura, y la lógica nueva debe ir reemplazando la antigua a medida que se complete la migración.
