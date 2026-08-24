# Finalización de acompañamiento

## Fecha

2026-08-14

## Problema

El proceso de admisiones de Alimentar Comunidad tiene tres etapas: Admisión,
Acompañamiento y Rendición de Cuentas. La tercera no está implementada, por lo
que las admisiones quedan abiertas al terminar el acompañamiento y las vigentes
conviven con las históricas compartiendo estado de avance.

Ante la falta de un cierre real del proceso, se estaba usando "Forzar Cierre"
—pensada para casos excepcionales de error o traba administrativa del
expediente, y disponible solo para administradores— como si fuera la marca de
finalización. Eso mezcla dos hechos distintos: una admisión cerrada por error
administrativo y un convenio cuyo plazo de ejecución terminó normalmente.

## Cambio

Se agrega la acción **Finalizar Acompañamiento** en el detalle del
acompañamiento, como estado propio y distinto de "Cerrado".

- `Acompanamiento` suma `fecha_finalizado` y `finalizado_por`, más las
  propiedades `finalizado`, `cerrado`, `puede_finalizarse` y `es_gestionable`.
- `AcompanamientoService.finalizar_acompanamiento(comedor, admision_id, user)`
  concentra las reglas y devuelve `(acompanamiento, error)`.
- Vista POST `finalizar_acompanamiento` + modal de confirmación con la leyenda
  acordada con producto.
- Los selectores de convenio del detalle de acompañamiento, del legajo comedor y
  de intervenciones etiquetan **Cerrado** (admisión inactiva) y **Finalizado**
  (acompañamiento finalizado). Antes la etiqueta decía "Cerrada".

## Decisiones

**El estado vive en `Acompanamiento`, no en `Admision`.** Marcarlo vía
`Admision.activa = False` haría que `Admision.save()` fuerce
`estado_mostrar = "Inactivada"`, volviendo indistinguible "finalizado" de
"cerrado por forzar cierre" — justo la separación que el requerimiento pide.
Finalizar no toca `activa` ni `estado_mostrar`.

**Forzar Cierre y Finalizar son excluyentes.** Si la admisión ya fue inactivada,
`puede_finalizarse` es `False` y el service rechaza la operación. La acción está
disponible desde que el comedor inicia el acompañamiento hasta que la admisión se
inactiva.

**Sin permisos nuevos.** La URL usa
`acompanamientos.view_informacionrelevante`, el mismo permiso que ya gatea el
detalle del acompañamiento. Quien hoy puede ver el acompañamiento (técnicos,
coordinadores, administradores) puede finalizarlo, sin altas de grupos ni de
permisos. Queda asentado el trade-off: es una acción irreversible gateada por un
permiso de lectura, decisión tomada para cumplir el requisito de no ampliar
permisos a los usuarios operativos.

## Textos

El requerimiento especificaba **un solo texto**, palabra por palabra: la
advertencia del modal de confirmación. Ese está calcado.

El resto del copy visible es propio, no salió del ticket:

- La franja del detalle ("Acompañamiento finalizado el … por … Finalizó el plazo
  de ejecución del convenio: ya no es posible operar con esta admisión en
  SISOC").
- El botón "Confirmar finalización" y el mensaje de éxito.
- Los mensajes de bloqueo al restaurar un hito o cargar una intervención.

Se agregaron porque el requerimiento pedía que el acompañamiento "no pueda
gestionarse" pero no definía cómo comunicarlo: si el botón sólo desaparece, el
usuario no distingue entre finalizado, cerrado o falta de permisos. La redacción
sigue a propósito la del modal, para que la confirmación y el estado hablen
igual. Es texto de template, sin lógica atada: cambiarlo es trivial si producto
prefiere otra redacción.

## Bloqueo de operación

Con el acompañamiento finalizado o cerrado (`es_gestionable == False`):

- `restaurar_hito` rechaza la restauración y los botones se renderizan
  deshabilitados.
- `IntervencionCreateView.form_valid` rechaza nuevas intervenciones contra esa
  admisión, y el legajo comedor oculta "Agregar intervención" para el convenio
  seleccionado.

## Pendiente de definición de producto

1. **Expedientes de Pagos** y **Seguimiento Mensual** cuelgan de `Comedor`, no de
   `Admision`, por lo que no pueden bloquearse por convenio sin definir qué pasa
   cuando un comedor tiene un convenio finalizado y otro vigente. Quedan
   operativos.
2. **Listado de acompañamientos.** Hoy la pantalla excluye lo inactivo
   (`activa=True` en el `Exists`, el `Prefetch` y los `Subquery` de
   `obtener_comedores_acompanamiento`) y su grano es una fila por comedor, no por
   acompañamiento. Persistir el histórico con etiquetas Cerrado/Finalizado
   requiere definir antes ese grano. No se modificó en esta entrega.

## Migración

`acompanamientos/0009_acompanamiento_fecha_finalizado_and_more`: aditiva, dos
campos nullable, sin backfill ni data migration. Los acompañamientos existentes
quedan como no finalizados, que es el estado correcto.

## Validación

- `tests/test_acompanamientos_finalizacion_db.py` (nuevo, 6 tests): reglas del
  service y del modelo, incluida la no inactivación de la admisión, el rechazo
  del segundo intento y el aislamiento por comedor.
- `tests/test_acompanamientos_views_unit.py`: 4 tests nuevos de la vista y del
  contexto del detalle.
- `tests/test_informes_complementarios_templates.py`: 2 tests nuevos de render
  (advertencia del modal, y estado finalizado sin acción ni restaurar).
- Selección `acompanamiento or comedor or intervencion or admision`: 555
  aprobados. `test_dashboard_uses_public_comedores_projection` falla también en
  árbol limpio; es previo y ajeno a este cambio.
