# CDI: ajuste literal de textos visibles en FormularioCDI

Fecha: 2026-03-27

## Contexto

Se solicitó una nueva pasada de corrección sobre los textos visibles de `FormularioCDI`,
manteniendo intactos los códigos internos, la estructura del formulario y la lógica de
ocultamiento condicional ya existente.

## Cambios aplicados

- Se mantuvo la centralización de copy en `centrodeinfancia/formulario_cdi_text_overrides.py`.
- Se ajustó `water_access.caneria_dentro_cdi` a `Por ceñería dentro del CDI`.
- Se ajustó `internet_access_quality_staff.estable_sin_acceso_personal` a
  `El l CDI cuenta con un servicio de internet relativamente estable al que accede el personal`.
- No se modificaron values internos, nombres de campos ni contratos del formulario.
- No se agregó lógica nueva: el ocultamiento condicional de `Seguridad Eléctrica`
  cuando no hay electricidad ya existía y se mantuvo.

## Validación

- Se actualizaron tests del formulario para verificar los textos finales visibles en
  las opciones afectadas.
