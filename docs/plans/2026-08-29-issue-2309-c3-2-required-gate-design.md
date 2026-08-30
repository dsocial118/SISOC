# #2309 — C3.2: gate requerido y build condicional de Dispositivos

## Decisión aprobada

El pipeline de Dispositivos publicará siempre el check
`dispositivos_build_gate` en los PR hacia `development`, `homologacion` y
`main`. El build y el manifiesto sólo se ejecutarán cuando el diff afecte
Dispositivos o uno de sus inputs declarados.

Con esto, un PR ajeno termina el gate explícitamente como `N/A`; un PR relevante
no puede pasar el gate sin un build local trazable exitoso. No se publican
imágenes, no se usan Environments, no se despliega y no se modifica
infraestructura.

## Diseño

1. El workflow deja de filtrar el evento por `paths` para que el gate exista en
   todos los PRs objetivo.
2. Un job de clasificación compara el SHA base y el SHA fuente autorizados con
   una lista única de inputs relevantes: `services/dispositivos/`, Compose,
   settings, Dockerfile, entrypoint, requirements, el workflow y el clasificador
   mismo.
3. `build_manifest` conserva el build C3.1 y sólo corre si la clasificación es
   relevante.
4. `dispositivos_build_gate` corre siempre. Falla si el clasificador falla o si
   un cambio relevante no termina `build_manifest` con éxito; para cambios
   ajenos informa `N/A` y termina con éxito.
5. `deploy_guard` exige sólo `dispositivos_build_gate`. Su espera de checks
   externos conserva la semántica actual de checks requeridos sin depender de un
   job que pueda no aparecer.

## Implementación y pruebas

El clasificador vivirá en `.github/scripts/` y se probará con `node --test`.
Las pruebas cubren, como mínimo:

- cambio de vertical/runtime/contratos;
- Dockerfile, Compose, settings y requirements;
- cambio al workflow o al propio clasificador;
- cambio ajeno que debe quedar `N/A`;
- mezcla de archivo ajeno y relevante.

El workflow ejecutará esas pruebas antes de aceptar la clasificación. El gate
será el único nombre nuevo que se agrega a la lista de `deploy_guard`.

## Riesgos y reversa

Un falso negativo de paths ocultaría un build necesario. Se mitiga usando una
lista centralizada, pruebas de matriz y haciendo relevantes los archivos que
definen el propio pipeline. El rollback elimina el gate y restaura el trigger
filtrado de C3.1; no requiere datos, imágenes publicadas ni cambios de ambiente.

## Fuera de alcance

- Comparación de manifiestos entre ambientes, deploy, restart o rollback por
  SHA: continúan pendientes de C3 posterior.
- Routing, identidad, health, observabilidad, schema o storage propios: C4/C5.
