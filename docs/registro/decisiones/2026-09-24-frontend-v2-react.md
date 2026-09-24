# 2026-09-24 — Front v2 en React: convivencia, ruteo por Django y stack común

## Estado

Aceptada como regla. Implementación pendiente. La primera tarea de la épica de
migración de front crea `frontends/`.

Guía operativa para devs: `docs/implementaciones/frontend_v2.md`.

## Contexto

- Hay apuro por migrar el front a React con el nuevo diseño de UI/UX. El primer
  módulo es Celiaquía (#2573); después sigue PAS, que ya tiene diseño nuevo, y
  al final todos los módulos.
- Hace falta que esa migración:
  - no complique el back;
  - no duplique lógica;
  - avance en la dirección del ADR
    `2026-08-27-dispositivos-servicio-independiente-monorepo.md`: monorepo,
    servicios desplegables por separado y contratos explícitos.
- La gente de UI/UX entregó una skill con el sistema de diseño
  (`tema-verde-institucional`, MUI).
- Ya existe una PWA React (SISOC-PWA-Espacios-Comunitarios) con un stack que
  conviene reutilizar.

## Decisión

Las definió el responsable técnico (juanikitro). Las marcadas como
*recomendación del agente* surgieron de la propuesta del agente y fueron
aceptadas.

1. **Convivencia por prefijo.**
   - El front nuevo vive en `/v2/<modulo>/`; el viejo sigue en su ruta actual.
   - El menú viejo sigue apuntando al viejo; al nuevo se entra por URL.
   - Pasar el menú a `/v2/` y borrar pantallas viejas queda fuera de alcance
     por ahora.
2. **Monorepo, estructura híbrida.**
   - `frontends/apps/<modulo>/`: una app por módulo, cada una con su servicio
     de compose.
   - `frontends/packages/*`: paquetes internos compartidos (UI y cliente de
     API), no publicados.
3. **Stack alineado con las PWA.** React 19, Vite 7, TypeScript 5.9, React
   Router 7, TanStack Query 5, axios, react-hook-form y zod, con **versiones
   exactas** y un único lockfile. Node 22.14.0, como la PWA.
4. **Diseño con la skill de UI/UX.**
   - MUI 9 con el tema `tema-verde-institucional`, que vive una sola vez en un
     paquete compartido.
   - No se usa Tailwind en `/v2/`.
5. **Ruteo por Django.**
   - El Nginx del host no cambia. Django recibe `/v2/<modulo>/` y lo reenvía al
     servicio de front correspondiente, con allowlist por configuración y login
     obligatorio.
   - Decidido por el responsable técnico: todo debe pasar por Django, y Django
     distribuye.
6. **Sesión Django en el mismo dominio**, con CSRF. No hay tokens en el
   navegador.
   - Sin sesión: redirige al login actual con `next`.
   - 403: pantalla "sin permiso".
7. **API bajo `/api/<modulo>/`** con las convenciones vigentes del repo:
   paginación DRF, errores estándar DRF, `snake_case` y fechas ISO 8601.
8. **Contrato por OpenAPI** (drf-spectacular), con tipos generados con
   `openapi-typescript` y chequeo en CI.
   - *Recomendación del agente*: `openapi-typescript` genera solo tipos, sin
     runtime nuevo, y convive con axios y TanStack Query, que ya usa la PWA.
9. **Compose.**
   - Cada front es un servicio `front_<modulo>` que depende de `django` sano.
   - Se agrega un healthcheck a `django` usando `/health/`.
   - Desarrollo con Vite y hot reload.
10. **Observabilidad.** Sentry con el mismo proyecto que el back.
11. **Revisión.** Los PRs de `/v2/` siguen el mismo CODEOWNERS que el resto del
    repo.

## Alternativas descartadas

- **Repo separado por front**, como los satélites PWA. Contradice el ADR de
  monorepo, parte el contrato de API en dos PRs y suma autenticación de runner
  contra repos privados.
- **Una sola app `/v2/` para todos los módulos.** Es más simple al inicio, pero
  acopla el deploy de todos los módulos.
- **Una app por módulo sin paquetes compartidos.** Duplica tema, layout y
  cliente de API.
- **Token en el navegador**, como las PWA. Obliga a un login separado, deja el
  token expuesto ante XSS con datos de salud e incomoda la convivencia con las
  pantallas Django.
- **Ruteo de `/v2/` en el Nginx del host.** Evita que los assets pasen por
  Gunicorn. Se descartó porque se decidió que todo el tráfico entre por Django
  y que Django distribuya.
- **Tailwind**, como la PWA. La skill de diseño está hecha sobre MUI, y mezclar
  los dos sistemas duplica estilos.
- **orval u otros generadores de clientes.** Agregan runtime y código generado
  más pesado; alcanzan los tipos más el cliente axios propio.

## Consecuencias

- Aparece un toolchain Node formal en el repo (`frontends/`), con CI propio
  para lint, typecheck, test, build y contrato.
- **Django pasa a ser la puerta de entrada del front v2.**
  - Un front caído devuelve 503 solo en su ruta, sin afectar al resto.
  - Con Gunicorn síncrono, los assets de `/v2/` consumen workers. Se mitiga con
    cache inmutable de assets con hash.
- Las API views nuevas reutilizan los services existentes. Las reglas de
  negocio no se duplican en React.
- `/api/users/me/` necesita aceptar sesión, o hace falta un equivalente. Es un
  cambio de autenticación a revisar en la primera tarea.

## Condiciones para revisar la decisión

- Saturación de workers de Gunicorn, o latencia de `/v2/` peor que la de las
  pantallas viejas en HML: evaluar servir los assets de `/v2/` desde Nginx.
- Necesidad de servir un front desde otro dominio: revisar sesión vs token.
- Un módulo que necesite servidor propio (SSR o BFF): revisar antes de agregar
  un runtime Node.
- La skill de UI/UX cambia de librería base: revisar la regla de MUI.
