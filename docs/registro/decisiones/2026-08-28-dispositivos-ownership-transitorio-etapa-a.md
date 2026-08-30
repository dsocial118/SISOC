# 2026-08-28 - Dispositivos: ownership transitorio de Etapa A

## Contexto

El servicio Dispositivos se independizará dentro del monorepo por etapas. C1
separa el núcleo canónico de la compatibilidad Django, sin introducir aún un
schema, storage, runtime ni tráfico propios. Declarar esos recursos como si ya
fueran del servicio produciría dos escritores o una migración sin corte.

## Decisión

Durante la Etapa A, el monolito conserva la titularidad operativa de los
recursos legacy. Sólo `services.dispositivos.monolith_compat` puede accederlos
directamente; `services.dispositivos.application` consume datos puros de los
contratos versionados `v1`.

| Recurso | Owner actual | Consumidor permitido | Contrato/límite | Salida prevista |
| --- | --- | --- | --- | --- |
| `dispositivos_dispositivo` y sus IDs | Monolito | `monolith_compat.app` | ORM legacy, un único escritor | C5: schema propiedad de Dispositivos |
| media `dispositivos/documentacion/` | Monolito | `monolith_compat.app` | referencia privada de archivo | C5: storage privado y migración aprobada |
| `core_provincia`, `core_municipio` | Core | `monolith_compat.adapters` | `catalog.v1`; sin QuerySets/modelos en `application` | C5: proyección local versionada |
| identidad, permisos y scopes | Users | `monolith_compat.adapters` | `identity.v1` y alcance territorial como datos | C4: identidad firmada en gateway |
| favoritos | Core | `monolith_compat.adapters` | `favorites.v1`; configuración serializable | contrato explícito posterior |

El `AppConfig.label = "dispositivos"`, las rutas y las migraciones continúan
en la compatibilidad para preservar tablas, IDs y enlaces actuales. No se
introduce una segunda escritura ni se autoriza a `application` a consultar
tablas `core_*` o `users_*`.

## Reversa

Mientras C5 no haya movido datos ni escritores, revertir C1 equivale a seguir
sirviendo exclusivamente el CRUD legacy: no existe información nueva que
reconciliar ni contrato externo que retirar. Cada salida futura requiere una
decisión específica de migración, validación y rollback.

## Evidencia

- `import-linter` prohíbe los imports cruzados desde `application`.
- `services/dispositivos/tests/unit/` valida identidad, scopes, catálogo y
  favoritos sin settings Django.
- `services/dispositivos/tests/integration/` ejecuta las regresiones Django de
  la compatibilidad por separado.
