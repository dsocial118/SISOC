# VAT: lista de espera editable desde el modal del panel de cursos

## Contexto (bug reportado)

En el panel de cursos del centro, el modal de edicion de una comision de curso:

1. No permitia configurar el limite de la lista de espera (el campo cupo nunca
   aparecia).
2. El checkbox "Acepta Lista de Espera" nunca se mostraba tildado aunque la
   comision la tuviera activa.

## Diagnostico

El backend ya soportaba el limite (`ComisionCurso.cupo_lista_espera`, migracion
0049, y `ComisionCursoForm` con validacion acepta→cupo obligatorio). Los
defectos estaban en la capa UI del panel:

- El boton "Editar" de la fila de comision no emitia `data-acepta-lista-espera`
  ni `data-cupo-lista-espera`, y el binder real del modal
  (`setupComisionCursoModal()` en `centro_detail.html`) poblaba todos los campos
  **excepto** esos dos. Ademas su `setFormValue` solo seteaba `.value`, que no
  funciona para checkboxes (`.checked`).
- El `<script>` inline del partial `centro_cursos_panel.html` que sincronizaba
  la visibilidad del campo cupo era **codigo muerto**: el panel se inyecta via
  `innerHTML` (fetch AJAX) y los scripts inline no se ejecutan en ese flujo.
- Consecuencia adicional grave: al guardar cualquier edicion desde el modal, el
  checkbox iba desmarcado en el POST y `ComisionCursoForm.clean()` **borraba
  silenciosamente** la lista de espera (acepta=False, cupo=None).

La misma funcionalidad en el detalle de comision (`comision_detail.html`) ya
estaba implementada correctamente y sirvio de referencia.

## Cambio

- `centro_cursos_panel.html`: el boton Editar emite
  `data-acepta-lista-espera` (`1/0`) y `data-cupo-lista-espera`. Se elimina el
  script inline muerto (con nota de por que el sync vive en `centro_detail`).
- `centro_detail.html` / `setupComisionCursoModal()`:
  - `setFormValue` soporta checkboxes (`.checked` + sync), igual que el detalle.
  - Nuevo `syncWaitlistCapacity()`: muestra/oculta el campo cupo segun el
    checkbox, lo marca `required` cuando esta activo y lo limpia al desactivar.
    Se re-vincula en cada inyeccion del panel (guard `comisionCursoModalBound`
    se resetea porque el modal se reemplaza con el HTML nuevo).
  - Modo edicion: puebla acepta + cupo desde los data-* (acepta antes que cupo
    para que el sync no pise el valor). Modo alta: `reset()` + sync (campo cupo
    oculto hasta tildar).

Comportamiento resultante (criterios del bug):
- Al activar la lista de espera aparece el campo de cantidad limite (required).
- El checkbox refleja el estado real de la comision al abrir el modal.
- Editar una comision ya no desactiva la lista de espera por accidente.

## Alcance

Aplica al camino activo `Curso`→`ComisionCurso`. El camino Fase 4
(`OfertaInstitucional`→`Comision`) tiene `acepta_lista_espera` pero su modelo no
posee `cupo_lista_espera`; queda fuera de este fix.

## Validacion

- `test_cursos_panel_boton_editar_emite_estado_lista_espera`: el panel emite
  `data-acepta-lista-espera="1"` + `data-cupo-lista-espera="7"` (y `"0"` para la
  comision sin espera).
- `test_comision_curso_update_persiste_lista_espera`: POST con acepta+cupo
  persiste (12) y POST sin acepta la limpia (comportamiento intencional).
- Suite `-k "comision or panel or curso"` en verde; djlint sin observaciones.
