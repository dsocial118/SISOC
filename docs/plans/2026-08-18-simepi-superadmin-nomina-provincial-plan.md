# 2026-08-18 - Plan de implementacion de descarga provincial superadmin

## Alcance

Implementar el diseño aprobado en
`docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-design.md` con un
cambio pequeno, compatible con la descarga EGP existente y sin tocar el
servicio que arma o deduplica la nomina.

## Paso 1 - Contrato backend y autorizacion

Archivos:

- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `centrodeinfancia/views_export.py`

Secuencia:

1. Agregar tests que fallen para descarga superadmin con provincia valida,
   seleccion ausente/invalida y parametro inyectado en una descarga EGP.
2. Resolver la provincia seleccionada solamente para superadmin.
3. Responder `400` antes de generar el PDF si la seleccion superadmin no es
   valida.
4. Mantener `403` para usuarios sin rol y el alcance unico para EGP.

## Paso 2 - Modal en el listado

Archivos:

- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `centrodeinfancia/views.py`
- `templates/components/search_bar.html`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html`

Secuencia:

1. Agregar tests que fallen para la visibilidad del boton, modal, selector
   requerido y opciones provinciales del superadmin.
2. Extender de manera optativa los botones adicionales para abrir un modal.
3. Cargar provincias ordenadas solamente en el contexto superadmin.
4. Renderizar en el listado el formulario `GET` con selector obligatorio.
5. Conservar el enlace directo para EGP y ocultar ambos flujos a usuarios
   comunes.

## Paso 3 - Validacion focal

Ejecutar:

1. Tests de `centrodeinfancia/tests/test_nomina_ninos_pdf.py`.
2. `black --check` sobre Python modificado.
3. `djlint --check` sobre templates modificados, si la version instalada
   admite el template actual sin reformatos amplios.
4. `pylint` focal sobre Python modificado.
5. `git diff --check` y revision manual del diff.

## Paso 4 - Publicacion y homologacion

1. Commit convencional y push de la rama existente.
2. Actualizar el PR abierto hacia `main` con el nuevo alcance.
3. Crear un PR incremental hacia `homologacion` desde la misma rama.
4. Esperar todos los checks requeridos, mergear solamente ese PR y verificar
   el despliegue de homologacion contra el SHA mergeado.
5. Mantener abierto el PR hacia `main` para su promocion posterior.

