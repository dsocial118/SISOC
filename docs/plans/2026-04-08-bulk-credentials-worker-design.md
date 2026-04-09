# 2026-04-08 - Diseño: credenciales masivas con job persistido y reanudable

## Problema

El envio masivo de credenciales hoy corre dentro de una request web. Cuando el
volumen de filas es grande o el SMTP queda lento durante `AUTH` o `DATA`, el
worker HTTP puede abortar la request y provocar `500`. Ademas, el operador no
tiene un estado persistido del lote ni una forma confiable de reanudar desde el
ultimo punto consistente.

## Objetivo

- Procesar lotes grandes sin depender del timeout de la request web.
- Cortar en la primera falla para que el operador retome exactamente desde ese
  punto.
- Persistir siempre el estado del lote, la causa del error y el ultimo usuario
  al que se le envio correctamente el mail.
- Permitir `Reanudar` usando el mismo archivo ya subido, sin obligar a armar un
  Excel nuevo.

## Enfoque elegido

Se implementa un job persistido en base de datos, procesado por un worker
dedicado separado del servidor web.

### Componentes

1. `BulkCredentialsJob`
   - Guarda el archivo original, tipo de envio, estado del lote, contadores,
     checkpoints y ultimo error.
   - Mantiene `next_row_index` para retomar exactamente desde la fila fallida.

2. `BulkCredentialsJobRow`
   - Guarda el resultado por fila ya intentada.
   - Tiene un registro unico por fila, con estado actual, cantidad de intentos,
     mensaje visible al usuario y si la password fue actualizada.

3. Worker dedicado
   - Management command que toma jobs `pending`, los procesa fila por fila y
     actualiza el estado persistido despues de cada paso relevante.
   - Si el worker se interrumpe mientras un job esta `processing`, el sistema lo
     marca como `failed` por stale timeout y deja disponible el boton
     `Reanudar`.

4. UI web
   - La pantalla de carga crea un job y redirige al detalle.
   - El detalle muestra estado, contadores, ultimo usuario enviado con exito,
     ultimo usuario intentado, causa del error y tabla de filas procesadas.
   - Si el job falla, aparece un boton `Reanudar`.

## Flujo

1. El operador sube el archivo y elige el tipo de envio.
2. La web crea un `BulkCredentialsJob`, guarda el archivo y responde rapido.
3. El worker toma el job y parsea el Excel fuera del request.
4. Procesa secuencialmente desde `next_row_index`.
5. Si una fila falla:
   - registra el error visible al usuario;
   - deja el job en `failed`;
   - conserva `last_successful_*`;
   - deja `next_row_index` apuntando a esa misma fila.
6. Si el operador pulsa `Reanudar`, el job vuelve a `pending` y el worker
   reintenta desde esa fila.

## Decisiones de diseño

- El lote se detiene en la primera falla por pedido funcional. No se continua
  con filas posteriores.
- El archivo fuente se conserva en el job y se vuelve a parsear al reanudar.
  Esto evita persistir todo el Excel desnormalizado en una sola columna grande y
  mantiene el archivo original como fuente de verdad del lote.
- El detalle por fila se persiste solo para filas ya intentadas. Las pendientes
  se infieren por `next_row_index` y `total_rows`.
- No se usa auto-refresh en la UI para evitar loops visuales; el operador puede
  refrescar manualmente la vista de detalle.

## Riesgos y mitigaciones

- Si el worker cae a mitad de un lote, el job podria quedar `processing`.
  Mitigacion: stale detection por `last_activity_at`, que lo pasa a `failed`
  con un mensaje claro y permite `Reanudar`.
- Si el SMTP sigue fallando sistematicamente, el job no produce `500`; queda en
  `failed` con la causa visible.
- Si el archivo es invalido, el worker deja el job en `failed` sin side
  effects parciales.

## Validacion prevista

- Tests de service para:
  - crear job;
  - procesar exitosamente;
  - detenerse en primera falla;
  - reanudar desde la fila fallida;
  - marcar jobs stale como fallidos.
- Tests de views para:
  - permisos;
  - alta de job;
  - detalle;
  - boton reanudar.
- Tests del management command para confirmar que procesa jobs pendientes.
