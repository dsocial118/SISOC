# Cierre del ratchet arquitectónico de Fase 0

## Resultado

Las excepciones runtime de los contratos `core`, `ciudadanos` y `users` fueron
retiradas. El baseline remanente contiene únicamente dos herramientas locales
de `core`:

- `core.debug_queries -> **`: script de diagnóstico manual que carga vistas y
  modelos de dominio fuera del arranque de la aplicación.
- `core.benchmarks.** -> **`: bootstrap de benchmarks que crea datos de varios
  dominios y no participa de requests ni comandos operativos.

Ambas exclusiones son explícitas en `.importlinter` y se mantienen fuera del
alcance runtime de Fase 0.

## Garantía del contrato

Además de la corrida positiva de `lint-imports`, se inyectó temporalmente un
import directo `users -> comedores.models`. El contrato de Users falló con esa
dependencia y volvió a pasar al retirar la sonda. Esto confirma que una nueva
violación directa no puede ingresar al baseline vacío de Users.

La ruleset activa `Proteccion` exige el status `architecture_imports` para las
ramas `development`, `homologacion` y `main`; por tanto la garantía participa
del gate efectivo de integración.
