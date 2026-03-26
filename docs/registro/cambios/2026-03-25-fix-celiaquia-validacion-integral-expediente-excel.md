# Fix validación integral de Excel en expediente de Celiaquía

Fecha: 2026-03-25

## Problema

La validación del Excel de expediente no era consistente entre:

- importación inicial,
- edición de `RegistroErroneo`,
- y reproceso manual.

Eso generaba varios desvíos:

- algunos errores semánticos del responsable se degradaban a warning y dejaban avanzar la fila;
- edición y reproceso no reutilizaban la misma validación de campos;
- podían quedar altas parciales si una fila fallaba después de crear el beneficiario;
- `email_responsable`, `telefono_responsable`, `nacionalidad` y `localidad_responsable` no se validaban con el mismo nivel de precisión que el resto.

## Cambios realizados

- Se endureció la validación de importación:
  - campos numéricos no aceptan texto no numérico;
  - `nacionalidad` requiere ID válido o nombre exacto;
  - `email` y `email_responsable` invalidan la fila si vienen informados con formato inválido;
  - `telefono` y `telefono_responsable` siguen siendo opcionales, pero si vienen informados deben cumplir validación;
  - `localidad_responsable` ahora exige coincidencia exacta o ID válido dentro de la provincia del usuario.
- Se agregó un helper compartido para validar y normalizar la fila completa, reutilizado desde:
  - edición de `RegistroErroneo`;
  - reproceso de registros erróneos.
- Se movió la validación del responsable antes de consolidar la fila como válida.
- Se agregó rollback por fila en la importación para evitar buffers y estados parciales cuando falla el responsable después del beneficiario.
- El reproceso manual ahora usa la misma validación y se ejecuta con transacción por registro, evitando persistencias parciales.
- Si una fila es inválida, se conserva toda la información recuperable en `RegistroErroneo`, pero no se persisten legajos parciales de esa fila.

## Impacto

- Se mantiene la regla de obligatoriedad actual: solo se exigen los campos obligatorios definidos por el flujo.
- Los campos opcionales ya no bloquean por ausencia, pero sí por formato inválido cuando vienen cargados.
- Se reduce el riesgo de inconsistencias entre importación inicial, edición y reproceso.
