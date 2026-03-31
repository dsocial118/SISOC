# Cambio: FormularioCDI para Centro de Infancia

Fecha: 2026-03-13

## Que se agrega
- Modelo `FormularioCDI` vinculado a `CentroDeInfancia`.
- Modelos hijos para:
  - distribucion de salas
  - lista de espera por grupo etario
  - articulaciones institucionales
- Campo estable `cdi_code` en `CentroDeInfancia`.
- CRUD web de formularios CDI dentro de `centrodeinfancia`.
- Card `Formularios` en el detalle del CDI con las últimas 3 instancias.

## Criterios aplicados
- Se implementa la version principal del cuestionario, sin preguntas alternativas sugeridas.
- Los campos sin obligatoriedad funcional confirmada quedan opcionales.
- `qualified_teacher_coverage` mantiene 4 opciones cerradas.
- No se incorporan catálogos BAHRA en esta fase.

## Validacion prevista
- Tests de forms para reglas condicionales.
- Tests de scope por provincia.
- Test del resumen de últimas 3 instancias en detalle de CDI.

## Ajustes posteriores
- El formulario web limpia en backend y UI los campos ocultos por skip logic para no bloquear el guardado con valores residuales.
- La pantalla de alta/edición agrupa `Meses de funcionamiento del CDI` y `Días de funcionamiento del CDI` en la misma fila.
- Las tablas muestran errores por celda cuando una fila no valida.
- `source_form_version` deja de validarse como input de usuario en la pantalla web y se toma del default del modelo para evitar rechazos invisibles al guardar.
