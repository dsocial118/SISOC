# Cambio: revisión QA de DataCalle — alcance provincial en la planificación

## Alcance

Primer bloque de la revisión QA del 2026-09-16 (§5.2 del canal de
coordinación): los ítems de la pantalla de planificación de relevamientos.

## Comportamiento

- **QA-0008.** Si el coordinador tiene una sola provincia en su alcance, el
  selector viene resuelto y bloqueado: ya no la elige. El campo queda
  `disabled`, así que además Django ignora cualquier provincia que llegue por
  POST y usa la del alcance.
- El selector de municipios respeta el alcance territorial: si baja a nivel
  municipio, no ofrece la provincia entera.
- **QA-0010 y QA-0013.** Dispositivos y equipo se acotan a la **provincia
  elegida en el operativo**, no al alcance completo del actor, que para un
  administrador nacional era el país entero. Se recargan por cascada al cambiar
  la provincia, con endpoints propios que vuelven a aplicar el alcance del
  actor en el servidor.
- **QA-0009.** El área operativa se pide al elegir "Espacio público", no recién
  al guardar.
- **QA-0011.** Enlace para dar de alta un dispositivo que no está en el
  catálogo, visible sólo con permiso para crearlos.

## Decisiones

- La provincia bloqueada usa `disabled` en lugar de `readonly`: es la única
  forma en Django de que el valor enviado no se tenga en cuenta, así que cierra
  la puerta a planificar fuera del alcance manipulando el POST.
- Los endpoints de la cascada no confían en el parámetro: reaplican el alcance
  del usuario, de modo que pedir otra provincia por URL devuelve vacío.
