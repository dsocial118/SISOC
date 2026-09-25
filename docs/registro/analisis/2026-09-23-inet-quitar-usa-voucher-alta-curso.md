# REQ — Ocultar la opción "Usa voucher" del alta de curso

| | |
|---|---|
| **Tipo** | Corrección / depuración funcional |
| **Sistema / Módulo** | SISOC — INET/VAT, alta y edición de Curso |
| **Estado** | Implementado |

## Situación actual

El modal *Nuevo Curso* ofrece dos casillas mutuamente excluyentes: **"Usa
voucher"** e **"Inscripción libre"**. El propio modelo las rechaza si se marcan
juntas (`Curso.clean()`: *"Un curso no puede usar voucher e inscripción libre al
mismo tiempo"*). La opción de voucher no está en uso y confunde al operador.

Al marcar "Usa voucher" el formulario habilita además dos campos dependientes:
**costo en créditos** y **parametrías de voucher**, ambos obligatorios en ese
caso.

**El área ya migró todos los cursos que tenían voucher activo a inscripción
libre**, por lo que no queda operación en curso dependiendo de esa opción.

## Objetivo

Dejar **"Inscripción libre"** como única opción visible en el alta y edición de
curso. El campo y su lógica **se ocultan, no se eliminan**: la funcionalidad de
voucher se va a volver a necesitar más adelante y debe poder reactivarse a bajo
costo.

## Alcance

**Incluye:**

| Capa | A modificar |
|---|---|
| `VAT/forms.py` | `CursoForm`: campos `usa_voucher`, `costo_creditos` y `voucher_parametrias`, y su validación cruzada en `clean()` |
| `centro_cursos_panel.html` | Render de las casillas y de los campos dependientes (~líneas 337-375) y los `data-*` del botón Editar |
| `centro_detail.html` | Lógica JS que muestra/oculta los campos según la casilla (~líneas 2958, 3786, 4091-4151) |

**No incluye:** la columna `Curso.usa_voucher` ni sus datos; la lógica de
inscripción con voucher en `InscripcionService`; el módulo de vouchers y
parametrías; `OfertaInstitucional.usa_voucher`, que es un camino aparte.

## Requerimiento funcional

1. Quitar del alta y la edición de curso la casilla "Usa voucher" y los campos
   que solo aplican con voucher (costo en créditos y parametrías).
2. Los cursos nuevos quedan con `usa_voucher = False`, que ya es el valor por
   defecto del modelo. `clean()` además fuerza `costo_creditos = 0` en ese caso,
   así que no hace falta migración ni valores especiales.
3. Retirar la validación cruzada con "Inscripción libre": sin la casilla, el
   conflicto no puede darse desde la aplicación.
4. Limpiar el JS que mostraba y ocultaba los campos dependientes.
5. **No** eliminar la columna ni la lógica de inscripción con voucher: debe
   seguir operativa para cuando se reactive la funcionalidad.
6. **No** introducir un feature flag ni código muerto para "apagar" la opción:
   se quita de la interfaz y la reactivación se resuelve revirtiendo el cambio
   desde el historial de Git. Es la vía más simple y deja el código limpio.

## Criterios de aceptación

- [ ] El modal de alta y el de edición de curso no muestran "Usa voucher",
      costo en créditos ni parametrías de voucher.
- [ ] "Inscripción libre" sigue disponible y funcionando.
- [ ] Se puede crear y editar un curso sin errores de validación.
- [ ] La columna `usa_voucher`, el módulo de vouchers y la lógica de descuento
      de créditos siguen existiendo y sin cambios.
- [ ] Editar un curso no altera el valor de `usa_voucher` que tenga guardado.

## Riesgos

- Desde la aplicación no se podrán crear cursos con voucher mientras dure la
  ocultación. **Es el comportamiento buscado**, y el área ya migró los cursos
  que la usaban.
- Aunque no debería quedar ninguno, si sobrevive algún curso con voucher activo
  el formulario ya no mostrará esos campos: el guardado tiene que **conservar**
  los valores almacenados en lugar de pisarlos con los valores por defecto.
- La clasificación "Tipo de alumno" (VAT / Sin Plan) **no** se ve afectada:
  depende del voucher activo del ciudadano, no de `Curso.usa_voucher`.
