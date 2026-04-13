# Fix VAT en detalle de ciudadano

Fecha: 2026-04-10

## Contexto

Al abrir el detalle de un ciudadano en:

- `ciudadanos/ver/<pk>`

la vista `CiudadanosDetailView.get_vat_context()` intentaba cargar datos de VAT y
producía un error en producción:

```text
django.core.exceptions.FieldError: Invalid field name(s) given in select_related:
'titulo_referencia'
```

El error se registraba desde `ciudadanos/views.py` al evaluar consultas sobre
`Inscripcion` e `InscripcionOferta`.

## Causa raíz

En VAT, `PlanVersionCurricular.titulo_referencia` ya no es una relación ORM
directa apta para `select_related`, sino una `@property` de compatibilidad que
resuelve el primer elemento de la relación `titulos`.

Por eso, estas consultas eran inválidas:

- `comision__oferta__plan_curricular__titulo_referencia`
- `oferta__oferta__plan_curricular__titulo_referencia`

`select_related()` solo acepta relaciones navegables del ORM (`ForeignKey` /
`OneToOne`), no propiedades Python.

## Cambio aplicado

En `ciudadanos/views.py`:

- se removió `plan_curricular__titulo_referencia` de `select_related()`,
- se agregó `prefetch_related(...__titulos)` en las consultas VAT afectadas.

En `tests/test_ciudadanos_views_unit.py`:

- se ajustó el mock de queryset usado por el test del contexto VAT,
- el mock ahora soporta `prefetch_related()` además de `select_related()` y
  `order_by()`.

Esto fue necesario porque el test anterior simulaba una cadena ORM más corta que
la usada por la vista antes del fix. El objetivo funcional del test no cambió:
sigue validando el resumen por programa del bloque VAT.

## Impacto funcional

No cambia el comportamiento esperado para el usuario final.

El ajuste corrige únicamente la estrategia de carga de datos del ORM para que el
bloque VAT del detalle de ciudadano no falle al construir el contexto.

## Riesgos y notas

- El cambio evita el `FieldError`, pero conviene observar si el bloque VAT sigue
  mostrando el título esperado cuando existen múltiples títulos asociados al
  mismo plan curricular.
- La propiedad `titulo_referencia` mantiene el criterio actual: devolver el
  primer título por `id`.

## Validación

- Se replicó el error localmente al abrir el detalle de un ciudadano con datos
  VAT.
- Se verificó el modelo VAT y la definición de `titulo_referencia` para ajustar
  la consulta al contrato real del ORM.
- Se actualizó el test unitario afectado para reflejar la nueva cadena ORM
  (`select_related() -> prefetch_related() -> order_by()`).
- No se pudo ejecutar la suite local de tests en este entorno porque faltan
  dependencias instaladas (`ModuleNotFoundError: rest_framework`).
