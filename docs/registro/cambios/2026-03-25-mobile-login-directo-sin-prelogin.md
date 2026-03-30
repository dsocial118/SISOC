## Cambio

Se removio el `PreLogin` del flujo inicial de Mobile para que la app abra directamente en la pantalla de login.

## Implementacion

- Se actualizo `mobile/src/app/router.tsx` para redirigir `/` y rutas publicas desconocidas a `/login`.
- Se elimino la redireccion inicial que forzaba la entrada a `/`, porque mantenia el paso por `PreLogin`.
- Se ajusto `mobile/src/auth/ProtectedRoute.tsx` para que una sesion no autenticada vuelva a `/login`.
- Se movio `InstallPwaModal` al formulario de login y se eliminaron los archivos viejos del flujo publico anterior.
- Se removio el splash de carga del arranque publico para que el login renderice de inmediato mientras se valida la sesion.

## Impacto

- Al entrar a Mobile se muestra directamente el formulario de acceso.
- La card de instalacion PWA sigue disponible, pero ahora aparece en login.
- Se eliminaron `PreLoginPage` y `LoginPage`, que ya no participaban del flujo actual.
- Si existe una sesion valida, el login redirige automaticamente al home correspondiente sin mostrar la pantalla de carga inicial.
- Las rutas protegidas siguen requiriendo autenticacion y redirigen al login cuando corresponde.
