# #2309 — C1: límite de servicio dentro del monorepo

## Decisión confirmada

SISOC mantiene un único repositorio. Dispositivos será un servicio desplegable
de forma independiente dentro de ese monorepo, no un repositorio nuevo.

Durante la Etapa A, el ORM legacy, sus FKs hacia `core` y el CRUD Django actual
permanecen en una capa de compatibilidad del monolito. El paquete canónico del
servicio no importará `core` ni `users`, ni consultará tablas de otros
verticales. Los catálogos, la identidad, el alcance territorial y los favoritos
se reciben por contratos versionados.

## Objetivo verificable de C1

Dejar una frontera de código comprobable y reversible, preparada para que C2
agregue build y arranque independiente. C1 no mueve tráfico, no crea una imagen
ni un Compose, no ejecuta migraciones independientes y no modifica datos.

## Topología objetivo

```
services/dispositivos/
├── application/                 # núcleo canónico, sin Django monolítico
│   ├── contracts/v1/             # identidad, territorio, catálogos, favoritos
│   ├── ports/                    # interfaces de entrada/salida
│   └── use_cases/                # reglas reutilizables y DTOs
├── monolith_compat/              # único consumidor Django temporal
│   ├── app/                      # modelos/FKs, forms, vistas, templates, URLs
│   └── adapters/                 # sesión users, core, filtros y permisos
└── tests/
    ├── unit/                     # application, sin settings del monolito
    └── integration/              # compatibilidad Django existente
```

El `AppConfig.label = "dispositivos"`, las migraciones y la tabla
`dispositivos_dispositivo` viven en `monolith_compat/app` durante la Etapa A.
Así se conserva el contrato del monolito sin fingir que ese ORM es la
persistencia independiente del futuro servicio.

## Contratos v1 de C1

Los contratos son datos y puertos, no imports de modelos o QuerySets:

| Contrato | Datos mínimos | Proveedor temporal | Salida |
| --- | --- | --- | --- |
| `identity.v1` | actor, autenticación, permisos | sesión Django del monolito | gateway/JWS en C4 |
| `territory.v1` | provincia, municipio, alcance | `users` mediante adaptador | autorización local del servicio |
| `catalog.v1` | IDs y nombres de provincia/municipio, versión | adaptador `core` | proyección propiedad de Dispositivos |
| `favorites.v1` | sección, filtros y operaciones permitidas | filtros favoritos de `core` | contrato HTTP opcional posterior |

Cada contrato declara versión, dueño, consumidor, semántica de ausencia/error y
prueba de compatibilidad. C1 no decide JWT, JWKS, gateway ni transporte HTTP.

## Registro de ownership temporal

| Recurso | Owner actual | Consumidor permitido en Etapa A | Contrato | Salida | Reversa |
| --- | --- | --- | --- | --- | --- |
| `dispositivos_dispositivo` | monolito | `monolith_compat` | modelo legacy temporal | C5, schema propio | volver a app legacy, sin datos nuevos |
| media `dispositivos/documentacion/` | monolito | `monolith_compat` | referencia privada de archivo | C5, storage privado | fuente legacy read-only |
| `core_provincia`, `core_municipio` | Core | sólo adaptador de catálogo | `catalog.v1` | C5, proyección local | usar catálogo Core vigente |
| identidad, permisos y scopes | Users | sólo adaptador de identidad | `identity.v1`, `territory.v1` | C4, identidad firmada | monolito conserva sesión |
| favoritos | Core | sólo adaptador de favoritos | `favorites.v1` | contrato explícito posterior | registro actual Core |

Ningún paquete bajo `application/` puede importar o consultar estos recursos
directamente. La excepción legacy queda acotada a `monolith_compat` y se elimina
en C5.

## Plan de ejecución

### C1.1 — Rebaselinar el PR y congelar la frontera

1. Corregir el checklist del PR: C1 queda en 40–45%; el movimiento físico no
   equivale a runtime ni despliegue independiente.
2. Marcar como supersedido el diseño de reubicación anterior para evitar que su
   catálogo read-only directo se interprete como diseño final.
3. Añadir contratos `v1` con tests unitarios sin Django monolítico.

**Salida:** contratos revisables, sin decisión de transporte ni infraestructura.

### C1.2 — Separar el legado del núcleo canónico

1. Trasladar modelos, migraciones, forms, vistas, URLs, templates y tests de
   regresión al paquete `monolith_compat/app`, conservando label, nombres de
   rutas, tablas e IDs.
2. Mover los adaptadores de sesión, permisos, filtros y catálogo a
   `monolith_compat/adapters`.
3. Eliminar del paquete canónico el modelo espejo `shared_catalog` y cualquier
   acceso directo a tablas `core_*`.
4. Mantener `config/settings.py` y `config/urls.py` apuntando exclusivamente a
   la capa de compatibilidad mientras no haya routing independiente.

**Salida:** sólo la compatibilidad conoce Django, `core` y `users`; el núcleo no.

### C1.3 — Evidencia automática y ownership

1. Ajustar `import-linter` para prohibir en `application/` imports de
   `core`, `users`, la capa de compatibilidad y modelos Django del monolito.
2. Separar tests unitarios del núcleo de las integraciones Django legacy;
   ejecutar cada grupo por path en CI.
3. Registrar el ownership anterior como decisión temporal y agregar pruebas de
   contrato para permisos, scopes, catálogo y favoritos.
4. Ejecutar regresiones existentes de CRUD/rutas desde la capa de compatibilidad.

**Salida:** evidencia C1 de import boundaries, contratos y comportamiento legacy.

## Criterios para declarar C1 cerrado

- El núcleo canónico no importa modelos/internals ni toca tablas de otros
  verticales.
- La compatibilidad monolítica preserva rutas, permisos, alcance, tablas, IDs y
  un único escritor.
- Los contratos v1 y el ownership temporal están documentados y testeados.
- Las pruebas unitarias del núcleo y las de compatibilidad se ejecutan como
  grupos distintos.
- C2 puede agregar Dockerfile, Compose selectivo y job de migración sin mover
  de nuevo la lógica de negocio.

## Fuera de alcance explícito

Docker/Compose, imagen, job de migraciones, CI/CD de artefactos, gateway/JWS,
routing público, health, observabilidad, schema propio, storage propio y datos
reales. Esos temas pertenecen respectivamente a C2–C5.
