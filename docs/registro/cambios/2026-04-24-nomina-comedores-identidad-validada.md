# Nomina de comedores: identidad validada requerida

Fecha: 2026-04-24

## Cambio

La nomina de comedores solo puede incorporar ciudadanos que no esten pendientes de revision de identidad.

## Regla

- Si `Ciudadano.requiere_revision_manual=True`, el alta en `Nomina` se rechaza.
- Si la revision manual ya fue cerrada (`requiere_revision_manual=False`), el ciudadano puede ingresar aunque su origen haya sido un caso no validado por RENAPER.
- El bloqueo se aplica en `ComedorService.agregar_ciudadano_a_nomina`, compartido por nomina por admision y nomina directa.

## Impacto operativo

Los ciudadanos visibles en `/ciudadanos/revision/` no pueden ser agregados a la nomina de comedores hasta que su identidad sea validada por RENAPER o se cierre la revision manual.
