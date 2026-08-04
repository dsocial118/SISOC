# Módulos nuevos extraíbles

Guía compartida para desarrolladores y asistentes que creen un dominio nuevo
en SISOC o amplíen uno con una dependencia interdominio.

## Decisión

SISOC sigue siendo, por ahora, un **monolito Django modular**: un deployable y
una base MySQL. Los dominios nuevos se construyen para que puedan pasar más
adelante a un repositorio y deployable propios sin reescribir su lógica de
negocio ni desarmar imports cruzados.

Esto no pide crear un microservicio, un repositorio, settings separados, una
API HTTP interna, Redis ni una base nueva ahora. Compartir la misma base lógica
implica que esquema, migraciones e integridad referencial siguen coordinados.
La extracción sólo se hará cuando haya una razón operativa concreta (equipo,
ciclo de release o escala distintos).

La referencia estratégica es la issue #1931. Esta guía vuelve obligatoria su
criterio para código nuevo, sin exigir que las apps existentes se refactoricen
como parte de una feature.

## Estado real de SISOC que condiciona esta guía

- Las apps Django se cargan juntas en `config/settings.py` y sus rutas se
  componen hoy desde `config/urls.py`.
- `core`, `users` y `ciudadanos` cumplen hoy el papel práctico de kernel, pero
  todavía contienen deuda legacy y no son una API de dominio genérica.
- Hay un ratchet de imports en `.importlinter` para `core`, `users` y
  `ciudadanos`. Sus excepciones existentes son baseline legacy, no patrones a
  copiar.
- `api_views.py` y `api_urls.py` son superficies HTTP/DRF. No sustituyen la
  fachada Python entre dominios definida más abajo.
- Existen acoplamientos que la nueva arquitectura no debe repetir: por ejemplo,
  usos de RENAPER desde `centrodefamilia`, y dependencias de
  `centrodeinfancia` o `ver_para_ser_libre` hacia dominios del cluster de
  comedores.
- El cache actual es `LocMemCache` y el middleware conserva usuario en
  thread-local. Ninguno sirve como estado compartido entre deployables.

Por eso esta guía describe una **convención para módulos nuevos**, no declara
que las apps actuales ya sean extraíbles. Cada extracción futura requerirá su
propio relevamiento de dependencias, datos y despliegue.

## Clasificar antes de diseñar

Antes de escribir modelos o views, el responsable debe registrar en la issue o
PR una ficha breve con: nombre del dominio, dueño funcional, entidades/tablas
propias, dependencias, permisos, side effects y motivo de clasificación.

Elegir una sola clasificación:

1. **Vertical extraíble.** Puede depender sólo del kernel autorizado y es el
   objetivo de esta guía.
2. **Parte de un bounded context existente.** Si necesita transacciones,
   reglas o tablas de `comedores`/admisiones/relevamientos/organizaciones/u
   otro cluster inseparable, se declara así y no se promete extracción.
3. **Cambio de kernel compartido.** Es excepcional. Requiere una decisión de
   arquitectura separada; no se introduce un concepto de negocio en `core`
   sólo para desbloquear una feature.

Una dependencia que no encaja en el kernel no se disimula como un entero, SQL
manual o señal. Se diseña el contrato explícito o se reclasifica el alcance.

## Kernel permitido para un vertical extraíble

El kernel es una lista explícita, no todo lo que hoy vive en `core`:

- identidad y actor mediante `settings.AUTH_USER_MODEL`;
- `Ciudadano`, cuando el dominio realmente lo referencia;
- territorial y catálogos estables de `core` (`Provincia`, `Municipio`,
  `Localidad`, `Programa`, etc.), sólo los que se declaren en la ficha;
- utilidades técnicas transversales ya existentes, como soft-delete, sólo si
  no llevan una regla de negocio ajena.

No son dependencias permitidas por defecto: `organizaciones`, `comedores`,
`intervenciones`, otra app vertical, una view, un form, un task, un signal o un
cliente externo que pertenezca a otro dominio.

Si el módulo necesita datos o una operación de otro vertical, debe llamar su
fachada pública. Si esa fachada no existe, el trabajo se divide: primero el
contrato/boundary y después la feature. No se agrega un import directo como
atajo.

## Forma mínima del módulo hoy

Seguir los patrones actuales de Django; no imponer capas nuevas sólo por la
extracción futura. La diferencia obligatoria es una fachada pública pequeña:

```text
nuevo_modulo/
  apps.py
  models.py
  migrations/
  services/
  api.py              # contrato Python público entre dominios
  views.py o views/   # UI propia, si aplica
  api_views.py        # HTTP/DRF, sólo si el caso lo requiere
  urls.py / api_urls.py
  tests/
```

`nuevo_modulo/api.py`:

- recibe IDs primitivos o comandos/DTOs simples;
- devuelve dicts, dataclasses u otros DTOs estables;
- nunca recibe ni devuelve `HttpRequest`, `ModelForm`, modelos Django ni
  `QuerySet`;
- delega la regla de negocio a `services/` del propio módulo;
- es el único import permitido desde otro dominio para consumir esa capacidad.

Mientras el módulo vive dentro del monolito, la fachada llama código local. Al
extraerlo, el mismo contrato puede pasar a un cliente HTTP interno sin obligar a
cambiar a sus consumidores.

## Datos, ORM y migraciones

1. **Una tabla, un dueño.** El módulo crea, cambia y migra sólo sus tablas.
   Ninguna otra app modifica sus tablas mediante migraciones o escritura ORM.
2. **App label estable.** Elegir un nombre de app único y conservarlo al mover
   el módulo para que el historial de `django_migrations` siga siendo
   reconocible.
3. **Relaciones al kernel.** Una FK real desde una tabla propia hacia un modelo
   del kernel está permitida cuando aporta integridad y se declara. No reemplazar
   una relación necesaria por un ID anónimo sólo para ocultar el acoplamiento.
4. **Relaciones genéricas.** `ContentType` y `GenericForeignKey` que apunten
   fuera del módulo también son relaciones cross-domain: no se usan para eludir
   este contrato y requieren la misma declaración y revisión.
5. **Borrado explícito.** Para una referencia externa, documentar `on_delete`,
   retención y reversa. Un nuevo `CASCADE` desde kernel hacia el módulo requiere
   revisión de arquitectura: transfiere responsabilidad de datos entre dueños.
6. **Sin ORM cross-domain.** Fuera de la relación al kernel autorizada, una
   view o service no consulta `OtraApp.objects`, sus relaciones reversas ni sus
   tablas. Usa `otra_app.api`.
7. **Migraciones compatibles.** Las migraciones deben ser aditivas y admitir
   versiones de aplicación temporalmente desfasadas. La separación de repos no
   elimina la coordinación de cambios de esquema.

Al extraer un vertical, sus propias tablas seguirán con `managed=True` en el
proyecto dueño. Las tablas del kernel se mapearán como `managed=False`; una
escritura sobre datos compartidos se resolverá mediante un contrato interno,
no dando al nuevo servicio propiedad de esas tablas.

## Presentación, extensiones e integraciones

- La única conexión global normal al crear la app es agregarla a
  `INSTALLED_APPS` y hacer `include("nuevo_modulo.urls")` desde
  `config/urls.py`. No agregar imports directos de views de la app en
  configuración global; el import actual de una view de Celiaquía es legado,
  no precedente.
- El módulo es dueño de sus URLs, templates, estáticos y permisos. Usar
  namespaces que eviten colisiones al moverlo.
- No crear una integración de menú, sidebar o Ciudadano 360 haciendo que
  `core` o `ciudadanos` importen la app. SISOC todavía no tiene un registro de
  extensiones público para esos casos: abrir una tarea de boundary separada y
  conservar la feature aislada hasta definirlo.
- No reutilizar un cliente externo que viva en otra app (por ejemplo,
  `centrodefamilia.services.consulta_renaper`). Si falta una integración
  transversal, primero se debe definir y ubicar su contrato compartido; no
  propagar ese acoplamiento legacy.
- Pasar el actor de forma explícita a los services. No usar thread-local para
  decidir reglas de negocio ni auditoría.
- El cache puede ser sólo una optimización local. No guardar allí tokens,
  locks, permisos ni estado cuya corrección dependa de verse desde otro proceso.
- Los signals locales deben ser mínimos y documentados. Un signal no puede ser
  el mecanismo oculto para cambiar otro dominio.

## Contratos y validación obligatoria

Todo vertical nuevo debe agregar desde su primer PR un contrato de arquitectura
en `.importlinter`. El contrato debe impedir que otros dominios importen sus
internos y que el vertical importe internals de otros verticales. No se agrega
una nueva dependencia intencional a `ignore_imports` para hacer pasar CI.

La validación mínima del cambio incluye:

```powershell
lint-imports
git diff --check
```

Además, ejecutar los tests focalizados del módulo con el runtime Docker del
repo cuando el comportamiento cambie. Debe haber al menos un test de la
fachada `api.py` y una regresión del flujo que la usa. Las pruebas HTTP/DRF
existentes complementan esa cobertura, pero no prueban por sí solas el contrato
entre dominios.

## Criterio de listo para mover más adelante

Un módulo queda preparado para extracción si se puede copiar su código y sus
migraciones a otro repositorio, agregar un proyecto Django mínimo y reemplazar
sus adaptadores al kernel, sin:

- reescribir la lógica de negocio;
- buscar imports de `models`, `services`, `views`, `forms`, `tasks` o `signals`
  de otros dominios;
- transferir propiedad de tablas ajenas;
- depender de cache de proceso o thread-local;
- romper las URLs, permisos o contratos que ya consumía SISOC.

No es requisito crear ahora el repositorio, Docker, autenticación SSO,
settings separados, workers, colas ni APIs de red. Hacerlo antes de necesitarlo
agregaría complejidad sin reducir el acoplamiento actual.

## Checklist de PR

- [ ] Se clasificó el cambio: vertical extraíble, bounded context existente o
      cambio de kernel.
- [ ] La ficha enumera tablas propias, dependencias permitidas, permisos y
      side effects.
- [ ] Existe `api.py` con DTOs/IDs y ningún consumidor externo importa
      internals del módulo.
- [ ] No se agregó una FK, import, signal o transacción hacia otro vertical.
- [ ] El nombre de app y la propiedad de migraciones son estables.
- [ ] Se agregó o ajustó el contrato `import-linter` sin ampliar el baseline.
- [ ] Se documentaron y probaron las operaciones públicas y los casos de
      borrado/cache/integración que correspondan.

## Fuera de alcance de esta guía

Esta decisión no recategoriza ni modifica las apps existentes. En especial,
no convierte automáticamente Celiaquía, VAT, Centro de Familia, Centro de
Infancia, Dispositivos o Ver Para Ser Libre en servicios extraíbles. Cada uno
tiene acoplamientos históricos que deben medirse antes de una extracción.

Ver también:

- `docs/ia/ARCHITECTURE.md`
- `.importlinter`
- `docs/plans/2026-06-22-monolito-modular-fase-0.md`
- `docs/registro/decisiones/2026-07-21-modulos-nuevos-extraibles.md`
