# Front v2 (React) — reglas para migrar módulos

Estado: **vigente como regla; implementación pendiente**. Todavía no existe
`frontends/` en el repo. La primera tarea de la épica crea la base descrita acá.

Decisión y alternativas descartadas: `docs/registro/decisiones/2026-09-24-frontend-v2-react.md`.

Aplica a **todo módulo que migre su front a React** (primero Celiaquía, después
PAS; al final, todos). Si una tarea necesita romper una regla, se discute en la
épica antes de implementar, no dentro del PR.

## 1. Convivencia viejo / nuevo

- El front nuevo vive bajo **`/v2/<modulo>/`**. Ejemplo:
  `https://sisoc.secretarianaf.gob.ar/v2/celiaquia/expedientes/`.
- El front viejo sigue igual en su ruta actual (`/celiaquia/...`).
- **El menú viejo no enlaza a `/v2/`.** Al front nuevo se entra solo por URL.
  Pasar el menú a `/v2/` y borrar pantallas viejas queda fuera de alcance hasta
  que se decida explícitamente.
- Las dos versiones usan los **mismos services** del back. Nunca hay dos lógicas
  de negocio vivas.
- El rediseño solo se aplica en `/v2/`. No se tocan templates viejos para
  "parecerse" al diseño nuevo.

## 2. Estructura en el monorepo

```text
frontends/
  package.json          # npm workspaces + scripts comunes
  package-lock.json     # único lockfile de todo el front v2
  .nvmrc                # 22.14.0
  .npmrc                # save-exact=true
  tsconfig.base.json
  eslint.config.js
  Dockerfile            # ARG APP=<modulo>; targets dev y prod
  packages/
    ui/                 # @sisoc/ui: tema, layout v2, componentes compartidos
    api/                # @sisoc/api: cliente HTTP, manejo de sesión, tipos OpenAPI
  apps/
    celiaquia/          # base /v2/celiaquia/
    pas/                # base /v2/pas/
```

- **Una app por módulo** en `apps/<modulo>/`, con su propio servicio de compose
  e imagen.
- **Lo compartido va en paquetes internos** (`packages/*`). No se publican en
  npm; las apps los consumen como código fuente del workspace.
- Una app **no importa de otra app**. Lo que dos apps necesiten se mueve a un
  paquete.
- El front **no importa nada del back** ni lee archivos de apps Django.

## 3. Stack y versiones

Las versiones son **exactas** (sin `^` ni `~`) y viven en un único lockfile. El
stack base está alineado con las PWA existentes (SISOC-PWA-Espacios-Comunitarios).
La capa visual sigue la skill de UI/UX `tema-verde-institucional`.

### Runtime

| Componente | Versión | Nota |
| --- | --- | --- |
| Node | 22.14.0 | Igual que el Dockerfile de la PWA de Espacios Comunitarios |
| npm | el incluido en Node 22.14.0 | lockfile v3; instalar con `npm ci` |

### Dependencias

| Paquete | Versión | Uso |
| --- | --- | --- |
| react / react-dom | 19.2.4 | — |
| react-router-dom | 7.13.1 | ruteo dentro de cada app |
| @tanstack/react-query | 5.90.21 | estado de servidor, cache de requests |
| axios | 1.13.5 | cliente HTTP (dentro de `@sisoc/api`) |
| react-hook-form | 7.71.2 | formularios |
| @hookform/resolvers | 5.2.2 | — |
| zod | 4.3.6 | validación de formularios (solo UX) |
| @mui/material | 9.4.0 | componentes (tema de la skill) |
| @mui/icons-material | 9.4.0 | íconos |
| @emotion/react | 11.14.0 | requerido por MUI |
| @emotion/styled | 11.14.1 | requerido por MUI |
| @fontsource/roboto | 5.3.0 | Roboto autoalojada (300/400/500/700) |
| @sentry/react | 10.75.3 | errores del navegador |

### Herramientas de desarrollo

| Paquete | Versión |
| --- | --- |
| typescript | 5.9.3 |
| vite | 7.3.1 |
| @vitejs/plugin-react | 5.1.4 |
| eslint | 10.11.0 |
| @eslint/js | 10.0.1 |
| typescript-eslint | 8.70.1 |
| eslint-plugin-react-hooks | 7.1.1 |
| eslint-plugin-react-refresh | 0.5.7 |
| globals | 16.5.0 |
| openapi-typescript | 7.13.0 |
| vitest | 4.1.11 |
| jsdom | 29.1.1 |
| @testing-library/react | 16.3.3 |
| @testing-library/dom | 10.4.1 |
| @testing-library/jest-dom | 7.0.1 |
| @playwright/test | 1.63.0 |
| @types/react | 19.2.7 |
| @types/react-dom | 19.2.3 |
| @types/node | 24.10.1 |

Diferencias deliberadas con la PWA:

- **ESLint 10**, porque ESLint 9 figura sin soporte en npm.
- **MUI en lugar de Tailwind**, porque la skill de diseño está hecha sobre MUI.
  En `/v2/` no se mezclan Tailwind y MUI.
- **Íconos de `@mui/icons-material`**, en lugar de FontAwesome o lucide.

Qué se verificó:

- La combinación completa se instaló y pasó `tsc`, `vite build`, `vitest run` y
  `eslint`, con el `theme.ts` de la skill sin modificar, sobre Node 24 local
  (2026-09-24).
- Falta repetir esa corrida sobre Node 22.14.0 dentro del contenedor. Se hace
  en la primera tarea.

Política de actualización:

- No se suben versiones dentro de un PR de pantallas.
- Los parches y las correcciones de seguridad van en un PR dedicado.
- Las versiones mayores se deciden en la épica.
- Todas las apps de `frontends/` comparten las mismas versiones.

## 4. Diseño (skill `tema-verde-institucional`)

- El tema MUI (`buildTheme(mode)`) vive **una sola vez** en `@sisoc/ui`. Las
  apps no redefinen colores.
- Los componentes usan **roles del tema** (`primary`, `background`, `text`,
  `nav`, …), nunca hex sueltos.
- El modo por defecto es claro. La preferencia se guarda en `localStorage`
  (`app.theme`), siempre dentro de `try/catch`. Como todas las apps de `/v2/`
  comparten origen, la preferencia es común a todas.
- AppBar y Drawer usan la superficie `nav`. La sección activa se marca en ámbar.
- Contraste AA: texto ≥ 4,5:1; bordes de control y rellenos de botón ≥ 3:1.
- Los estados info/attention/pending son neutrales, **no un semáforo**. El verde
  es de marca, no significa "OK".
- Roboto se carga con `@fontsource/roboto`, no con CDN.
- El `main.tsx` de ejemplo de la skill se adapta con `import type { ReactNode }`.
  No se copia literal.

## 5. Layout y navegación de `/v2/`

- El layout (AppBar + Drawer) es **propio de `/v2/`**: vive en `@sisoc/ui` y no
  reutiliza ni modifica el sidebar viejo (`templates/includes/sidebar/opciones.html`).
- El Drawer lista los módulos de `/v2/` que el usuario tiene permitidos, según
  el contexto de usuario que devuelve la API.
- Pasar de un módulo a otro (`/v2/celiaquia/` → `/v2/pas/`) es una navegación de
  página completa, porque son apps distintas.

## 6. Ruteo: todo entra por Django

El Nginx del host **no cambia**: ya envía todo el tráfico a Django. Django
recibe `/v2/<modulo>/...` y lo reenvía al servicio de front de ese módulo.

Reglas del router de Django:

- **Allowlist.** Los módulos y sus destinos salen de configuración
  (`settings`/env), nunca del request. Un módulo desconocido devuelve 404.
- **Solo lectura.** Solo acepta `GET`/`HEAD`. No reenvía `Cookie` ni
  `Authorization` al servicio de front, porque el front estático no los necesita.
- **Login obligatorio.** Todo `/v2/` exige sesión. Sin sesión, redirige a
  `/login/?next=<ruta pedida>`.
- **Mismo stack de middleware** que el resto del sitio (sesión, CSP, auditoría,
  confirmación de perfil, cambio de password obligatorio).
- **Timeout corto.** Si el servicio de front está caído o no responde, Django
  devuelve 503 para esa ruta y sigue funcionando para el resto.
- **Sin lógica.** No transforma contenido ni inyecta datos: solo reenvía.
- **Cache.**
  - Assets con hash (`/v2/<modulo>/assets/*`):
    `Cache-Control: public, max-age=31536000, immutable`.
  - `index.html`: `no-cache`.
  - Así, cada asset pasa por Django una sola vez por deploy y por navegador.
- **Riesgo aceptado.** En los entornos de deploy, Django corre con Gunicorn
  síncrono (4 workers × 1 thread por defecto), así que servir assets ocupa
  workers.
  - Condición para revisar la decisión: saturación de workers o latencia de
    `/v2/` peor que la de las pantallas viejas en HML.
  - En ese caso, se evalúa servir los assets de `/v2/` desde Nginx.

## 7. Comunicación con el back

- **Canal único:** API HTTP JSON bajo `/api/<modulo>/` (por ejemplo
  `/api/celiaquia/`, `/api/pas/`).
  - El front no accede a la base.
  - El front no depende de templates ni del contexto de Django.
  - El back no conoce al front.
- **Archivos en el back:** `api_urls.py`, `api_views.py` y `api_serializers.py`
  de la app, como el resto del repo.
  - `<app>/api.py` **no se usa para esto**: es el contrato Python público entre
    módulos (`docs/ia/MODULAR_BOUNDARIES.md`).
- **La lógica sigue en `<app>/services/`.** Las API views son delgadas y
  reutilizan los mismos services que usan las vistas Django actuales.
  - React no replica reglas de negocio; solo hace validaciones de UX (zod).

### Convenciones de API

Son las mismas que ya usa el repo:

- **Nombres de campos:** `snake_case`, sin conversión a camelCase. El front usa
  los nombres tal como vienen en los tipos generados.
- **Paginación:** `PageNumberPagination` de DRF, con la respuesta
  `{count, next, previous, results}`.
  - Parámetros `page` y `page_size` (máximo 200), como `VAT/pagination.py`.
  - Paginar es obligatorio en listados.
- **Filtros y orden:** query params en `snake_case`.
- **Errores:** los estándar de DRF.
  - `{"detail": "..."}` para errores generales.
  - `{"campo": ["mensaje"]}` para validaciones.
  - No se inventan otros formatos.
- **Fechas:**
  - Fechas en ISO 8601 (`YYYY-MM-DD`).
  - Fecha y hora en ISO 8601 con offset. El back usa `USE_TZ` con
    `America/Argentina/Buenos_Aires`.
  - El front formatea para mostrar en `es-AR`.
- **Status:**
  - `401`: sin sesión.
  - `403`: sin permiso.
  - `404`: no existe o está fuera del alcance del usuario.
  - `400`: error de validación.
  - Las API de `/v2/` mantienen las clases de autenticación por defecto de DRF,
    para que un request sin sesión devuelva 401 y no 403.

### Contrato (OpenAPI)

- El schema de drf-spectacular es la fuente de verdad.
  - Se genera con `python manage.py spectacular`, porque `/api/schema/` solo se
    expone con `ENABLE_API_DOCS`.
  - Se versiona en `frontends/packages/api/openapi.yaml`.
- Los tipos TS se generan desde ese archivo con `openapi-typescript`. No se
  escriben a mano.
- **CI** falla si:
  - el schema versionado no coincide con el que genera el back;
  - los tipos no coinciden con el schema.
- Un cambio que rompe el contrato va en el **mismo PR** que el ajuste del front.

## 8. Sesión, seguridad y permisos

- **Autenticación:** sesión de Django en el mismo dominio. No hay tokens en el
  navegador.
- **CSRF:** `@sisoc/api` envía `X-CSRFToken`, leído de la cookie `csrftoken`,
  en todo método no seguro.
- **Respuestas de la API:**
  - `401`: `@sisoc/api` redirige con navegación completa a
    `/login/?next=<ruta actual>`.
  - `403` con sesión activa: pantalla "sin permiso". No redirige al login, para
    evitar loops.
- **Permisos:** cada endpoint valida los permisos del módulo y el alcance del
  usuario (por ejemplo, la provincia en Celiaquía).
  - Ocultar un botón no es control de acceso.
  - Entrar por URL a `/v2/` no saltea nada.
- **CSP:** el front respeta el CSP vigente (`config/middlewares/csp.py`).
  - Sin scripts inline en `index.html` (el build de Vite no los genera).
  - Sin CDNs fuera de los permitidos; fuentes autoalojadas.
- **Secretos:** el build no lleva secretos. Toda variable `VITE_*` es pública
  por definición.

## 9. Docker Compose y desarrollo local

- **Servicio:** cada app es un servicio propio, llamado `front_<modulo>` (por
  ejemplo `front_celiaquia`), con imagen construida desde `frontends/Dockerfile`
  (`ARG APP`).
- **Dependencia del back:** declara
  `depends_on: { django: { condition: service_healthy } }`.
  - El servicio `django` tiene un healthcheck contra el `/health/` existente.
  - Reiniciar un servicio de front no reinicia `django`, y viceversa.
- **Desarrollo:** target `dev` con Vite y hot reload, código montado como
  volumen y `node_modules` en volumen propio (patrón `compose.dev.yaml` de la
  PWA).
  - El navegador entra por Django (`/v2/<modulo>/`).
  - El websocket de HMR conecta directo al puerto de Vite (`server.hmr`),
    porque Django no reenvía websockets.
- **Producción:** target `prod` con el build estático servido por
  `nginx-unprivileged` (patrón de la PWA).
  - Puerto interno, sin exponer al host: solo lo alcanza Django por la red de
    compose.

## 10. Calidad y CI

Cuando cambia `frontends/**` o una API consumida por `/v2/`, CI corre:
`npm ci`, `lint`, `typecheck`, `test` (Vitest + Testing Library), `build` y el
chequeo de contrato.

- **Tests unitarios y de componentes:** junto al código de cada app o paquete.
- **E2E con Playwright:** solo para los flujos críticos que defina la tarea de
  cada módulo.
- **Revisión de PRs:** igual que el resto del repo (`.github/CODEOWNERS`).

## 11. Observabilidad

Sentry usa el **mismo proyecto que el back**, configurado con `@sisoc/api` /
`@sisoc/ui`:

- `environment` igual que el back del entorno.
- `release` = SHA del commit.
- Tag `frontend=v2-<modulo>`.
- `sendDefaultPii: false`, porque son datos de salud y sociales.
- Replays solo si el entorno del back los tiene activos, y siempre con
  `maskAllText` y `blockAllMedia` activos.

## 12. Deploy (HML / PRD)

- Los servicios `front_<modulo>` se agregan al compose de deploy y al flujo
  existente (`scripts/operacion/deploy_refresh.sh`, `.github/workflows/deploy.yml`).
  No se crea otra plataforma de deploy.
- La imagen se construye por entorno (variables `VITE_*` del entorno) y se
  etiqueta con el SHA.
- Si falla el build del front, falla el deploy antes de reemplazar el servicio
  anterior.
- No hay cambios en el Nginx del host.

## Pendientes (se resuelven en la primera tarea de la épica)

- Contexto de usuario con sesión: `/api/users/me/` hoy acepta solo
  `TokenAuthentication`. Hay que habilitarlo con sesión o definir un endpoint
  equivalente. Es un cambio de autenticación: requiere revisión.
- Ubicación del router `/v2/` en el back (propuesta: `core/`, sin imports de
  dominio, con los destinos en `settings`).
- Filtrado del schema versionado a las rutas que consume `/v2/`, si el schema
  completo genera ruido en CI.
- Validar la matriz de versiones sobre Node 22.14.0 dentro del contenedor.
