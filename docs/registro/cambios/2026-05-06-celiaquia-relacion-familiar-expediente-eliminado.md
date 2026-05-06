# Celiaquia: no heredar rol familiar desde expedientes eliminados

## Contexto

Las relaciones familiares se guardan globalmente en `ciudadanos_grupofamiliar`.
Si un expediente con una relacion responsable-hijo era eliminado y luego se
cargaba un expediente nuevo con los mismos ciudadanos pero sin datos de
responsable, la relacion global previa podia hacer que el responsable anterior
se mostrara como `Beneficiario y Responsable`.

## Cambio

Para calcular roles efectivos dentro del detalle del expediente y documentos
requeridos, las relaciones globales solo se consideran si el legajo activo del
expediente declara rol `responsable` o `beneficiario_y_responsable`.

Un legajo nuevo importado como `beneficiario` ya no se promueve visualmente ni
documentalmente por una relacion global que quedo de un expediente eliminado.

## Validacion

Se agrego una regresion en `celiaquia/tests/test_expediente_detail.py` que simula:

- expediente previo con relacion familiar;
- eliminacion por soft-delete;
- expediente nuevo con los mismos ciudadanos sin relacion declarada;
- verificacion de que el responsable anterior queda como `Beneficiario`.
