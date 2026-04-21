# Diseño VAT teléfono +54

Fecha: 2026-04-17

## Problema

El alta automática de ciudadanos desde la inscripción web VAT recibe teléfonos con formato internacional.
El límite actual de 30 caracteres es demasiado corto para variantes reales con `+54`, separadores e interno,
y eso termina delegando el rechazo al modelo o a la base.

## Decisión

Ampliar `ciudadanos.Ciudadano.telefono` y `telefono_alternativo` a 50 caracteres y publicar una migración
explícita para forzar el schema desplegado a texto compatible con teléfonos internacionales.

## Alcance

- Ajustar el modelo `Ciudadano`.
- Agregar migración.
- Cubrir el caso con test de modelo y aserción de regresión en el flujo VAT.
- Actualizar la documentación funcional mínima del endpoint.

## Validación

- Test unitario de modelo para un teléfono internacional formateado con `+54`.
- Test del flujo VAT que verifica que el teléfono se persiste sin perder formato.
