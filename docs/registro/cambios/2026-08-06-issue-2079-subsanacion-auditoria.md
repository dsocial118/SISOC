# Issue 2079: correcciones del flujo de revisión

## Contexto

En homologación se detectaron dos regresiones en el flujo de rendiciones:

- una presentación territorial subsanada exigía iniciar nuevamente la revisión;
- el inicio de la revisión de Auditoría fallaba al restablecer los documentos validados.

## Cambio

- Al volver a presentar correcciones durante la etapa territorial, la rendición retoma
  directamente el subestado `en_curso` y conserva la etapa de revisión documental.
- Al iniciar la revisión de Auditoría, primero se materializan los identificadores de
  los documentos vigentes validados y luego se actualizan por identificador. Esto evita
  una actualización con subconsulta sobre la misma tabla, incompatible con MySQL.

## Compatibilidad

La subsanación durante la revisión de Auditoría conserva el paso explícito desde
`subsanado` hacia `en_curso`, según la máquina de estados vigente.

## Validación

Se agregaron regresiones unitarias para ambos recorridos.
