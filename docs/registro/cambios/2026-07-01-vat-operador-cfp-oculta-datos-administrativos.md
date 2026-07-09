# VAT: Operador CFP no visualiza datos administrativos del centro

## Contexto

El perfil "Operador CFP" (rol referente de centro, `auth.role_referentecentrovat`
/ `auth.role_centroreferentevat`) veia todos los campos del formulario de edicion
del Centro de Formacion Profesional, incluidos datos administrativos que solo
requieren los administradores INET/SSE (o provinciales):

- Clase de institucion (`clase_institucion`)
- Tipo de gestion (`tipo_gestion`)
- Estado ETP (`situacion`)

El operador solo necesita informacion operativa basica: denominacion, CUE y
referente/s. Ademas, la vista de detalle del centro exponia "Sector de gestion"
(`tipo_gestion`) al operador.

## Cambio

Se restringe la visualizacion de los tres campos administrativos para el
Operador CFP, sin afectar a SSE ni a usuarios provinciales:

- Nuevo helper `es_operador_cfp(user)` en `VAT/services/access_scope.py`:
  referente de centro que NO es SSE ni provincial. Un usuario con doble rol
  (referente + administrador) conserva la vista completa.
- Formulario de edicion (`CentroAltaForm`): cuando el actor es Operador CFP, los
  campos `tipo_gestion`, `clase_institucion` y `situacion` se **eliminan** del
  form (`_remove_fields`), no solo se ocultan. Asi el valor no viaja en el HTML
  y cualquier POST manipulado con esos campos se ignora; en la edicion el
  `ModelForm` conserva el valor de DB. Se reutiliza el mismo conjunto de campos
  que ya restringia el perfil `INET_PROVINCIA`.
- Template `centro_create_form.html`: los tres campos se renderizan con guardas
  `{% if form.<campo> %}` para soportar su ausencia.
- Vista de detalle (`CentroDetailView`): nuevo flag de contexto
  `mostrar_datos_administrativos = not es_operador_cfp(user)`. El template
  `centro_detail.html` oculta el bloque "Sector de gestion" para el operador.

### Sin fuga en API/backend

- `CentroViewSet` y demas serializers de Centro usan `HasAPIKey`
  (server-to-server); no son accesibles con la sesion del operador, por lo que no
  constituyen un vector de fuga para el rol Operador CFP.
- Los endpoints AJAX de sesion (`centros_ajax`, paneles) no exponen estos campos.
- El unico dato administrativo visible por sesion del operador era "Sector de
  gestion" en el detalle, ahora gateado.

## Validacion

Se agregaron tests de regresion en `VAT/tests.py`:

- el form elimina `tipo_gestion`/`clase_institucion`/`situacion` para el Operador
  CFP y conserva los campos operativos (nombre, codigo, referentes);
- el form conserva los tres campos para administrador INET/SSE;
- un POST manipulado del Operador CFP a `vat_centro_update` no modifica los
  valores administrativos (se conservan los de DB);
- el detalle oculta "Sector de gestion" para el Operador CFP y lo muestra para
  administrador INET/SSE.
