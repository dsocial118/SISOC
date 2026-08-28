# #2309 — C2: empaquetado y arranque independiente

## Decisión aprobada

Dispositivos tendrá un runtime Django propio dentro del monorepo. Durante la
Etapa A, ese runtime carga el cierre transitorio de apps legacy requerido por
las FKs, señales y adaptadores de `monolith_compat`. No inicia el proceso web
del monolito ni sus workers, aunque el grafo de código legacy siga siendo una
dependencia temporal. El núcleo `services.dispositivos.application` continúa
sin imports de esos dominios.

El runtime no inicia procesos del monolito ni reutiliza su entrypoint. Web y
migraciones se ejecutan como procesos separados. C2 no recibe tráfico público:
la continuidad de `/dispositivos/`, gateway e identidad firmada pertenecen a
C4.

## Ownership de Etapa A

El servicio Dispositivos pasa a ser el único writer de
`dispositivos_dispositivo` en la topología C2. El monolito conserva
compatibilidad y routing sólo mientras C4 no haya trasladado el tráfico; ambos
procesos no se ejecutan en paralelo atendiendo escrituras. Esta regla es
operativa en C2 y será técnica en C4/C5 mediante routing y credenciales
separadas.

No se cambian schema, IDs, FKs, media ni datos en C2. La propiedad física del
schema y storage continúa siendo transitoria hasta C5.

## Topología objetivo

```
compose.dispositivos.yml
├── mysql                         # dependencia local de Etapa A
├── dispositivos-migrate          # migrate dispositivos --noinput
└── dispositivos-web              # Gunicorn; nunca migra al arrancar
        └── services/dispositivos/runtime/
            ├── settings.py
            ├── urls.py
            ├── wsgi.py
            └── entrypoint.py
```

La imagen de Dispositivos reutiliza `docker/django/Dockerfile` como base para
no duplicar dependencias, pero declara comandos, settings, URLs y entrypoint
propios; nunca invoca `docker/django/entrypoint.py`. La composición actual del
repositorio sigue siendo la integración opcional completa.

## Reglas de runtime

- `dispositivos-web` sólo espera la DB y levanta Gunicorn. No ejecuta
  `makemigrations`, `migrate`, fixtures, creación de usuarios ni tareas del
  monolito.
- `dispositivos-migrate` ejecuta exclusivamente
  `python manage.py migrate dispositivos --noinput` con los settings del
  servicio. Repetirlo sin cambios debe terminar correctamente y sin migraciones
  pendientes.
- Los settings del servicio cargan temporalmente el cierre de apps legacy que
  exige Django, pero sustituyen URLs, WSGI, entrypoint y proceso del monolito.
  No registran rutas ni workers ajenos en su proceso web.
- El Compose selectivo levanta MySQL y los procesos de Dispositivos, no el
  servicio `django`, OCR ni otros workers del Compose raíz.
- Desarrollo local usa esa MySQL como dependencia. La guía declara que el
  schema Core/Users es una precondición temporal de Etapa A; no se presenta
  como independencia de datos.

## Plan de implementación

### C2.1 — Shell de runtime y configuración

1. Crear el paquete `services/dispositivos/runtime` con settings, URL raíz,
   WSGI y entrypoint explícito por rol (`web` o `migrate`).
2. Añadir una imagen nombrada de Dispositivos y `compose.dispositivos.yml`,
   reutilizando el Dockerfile base sin modificar el Compose de integración
   existente.
3. Añadir una guía local con variables mínimas, puertos, dependencia MySQL y
   advertencia de writer único.

### C2.2 — Evidencia de procesos separados

1. Probar que web no contiene ni ejecuta comandos de migración.
2. Probar build, arranque, stop/restart aislados y que no se inicia el
   servicio Django del monolito.
3. Probar dos ejecuciones consecutivas del job de migración.

Implementación: el job `dispositivos_runtime` de CI ejecuta esta secuencia con
`compose.dispositivos.yml`. Su resultado verde es la evidencia pendiente para
dar por validado C2.2; no sustituye el cierre completo de C2.3.

### C2.3 — Cierre de checkpoint

1. Ejecutar las pruebas C2 en CI sin path filtering todavía.
2. Registrar los logs de build/arranque y límites transitorios.
3. Confirmar que C3 hereda un artefacto y no una composición global.

## Criterios de aceptación C2

- La imagen y el runtime de Dispositivos se construyen e inician sin arrancar
  ni reiniciar el proceso Django del monolito.
- Web no migra al arranque; el job separado es idempotente.
- La composición global se mantiene opcional para integración.
- Se documentan dependencias locales/mocks, puertos, secretos requeridos y la
  regla de un único writer.

## Fuera de alcance

No se agregan gateway, rutas públicas, sesiones compartidas, JWS, health,
observabilidad, path filtering, artefactos promovibles, despliegues, nuevos
schemas, credenciales productivas, migraciones de datos ni cambios sobre
QA/HML/PRD.

## Validación de viabilidad

Un registro Django con sólo `core`, `users` y Dispositivos falla los checks por
relaciones y señales hacia `duplas`, `comedores`, `organizaciones`,
`ciudadanos` e `intervenciones`. Por eso C2 no presenta ese subconjunto como
runtime aislado: la independencia de proceso se demuestra ahora y la reducción
del grafo de código queda explícitamente en C5.
