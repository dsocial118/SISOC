# 2026-06-02 — Issue #1799 (feedback punto 1): "Actualizar desde Legajo" dirigido (no sobreescribir)

Rama: `claude/issue-1799-fix-actualizar-dirigido`
Issue: [#1799](https://github.com/dsocial118/SISOC/issues/1799) (comentario 2026-06-02, punto 1)

## Problema

El revisor pidió que la alerta y la decisión del Req 1 funcionen para todas las
admisiones que conviven hoy —incluidas las legacy con 100% de la documentación
cargada admisión-side, en cualquier estado— **cuidando no sobreescribir la info que
ya opera en el sistema**.

La opción **"Actualizar Información desde Legajo Organización"** llamaba a
[resync_admision_desde_organizacion](../../../admisiones/services/admisiones_service/impl.py),
que hace un **reset total**: cambia `tipo_convenio`, resetea `estado` y **borra
TODOS los `ArchivoAdmision`** antes de re-materializar. Eso es correcto cuando
cambia el **Tipo de Entidad** (el convenio y su set documental cambian, #1605),
pero para un cambio **solo de documentación** destruye los documentos nativos /
cargados admisión-side que no tienen contraparte en la organización.

## Solución (decisión de producto: actualización DIRIGIDA)

- **Nuevo** `AdmisionService.actualizar_documentacion_desde_organizacion(admision, user)`:
  calcula el diff entre el snapshot (`AdmisionDocOrgSnapshot`) y el estado actual
  del legajo (reusa `_tokens_org_actuales`), y refresca **solo** los slots que
  cambiaron (agregados / modificados / quitados):
  - borra únicamente los `ArchivoAdmision` **de origen organizacional**
    (`archivo_organizacion_origen` no nulo) de esos slots;
  - re-materializa con `congelar_documentacion_organizacional` (aditivo: re-crea los
    borrados que siguen vigentes, saltea los que ya existen);
  - **preserva** los documentos nativos de la admisión y los de origen
    organizacional no modificados;
  - **no** toca `tipo_convenio` ni `estado`; refresca el snapshot al final.
- **Routing** en [resync_convenio_admision](../../../admisiones/views/web_views.py)
  (`accion == "actualizar"`): si cambió el Tipo de Entidad
  (`admision_desincronizada`) → reset total (comportamiento #1605); si solo cambió
  la documentación (`documentacion_desactualizada`) → actualización dirigida.
- `accion == "continuar"` sigue igual (ya preservaba via
  `aceptar_desincronizacion_admision`).

## Validación

Entorno local Windows (Docker apagado, ver memoria de validación):

- `python -m py_compile` + `python -m black --check` sobre impl.py / web_views.py /
  test → OK.
- Tests nuevos: [admisiones/tests/test_actualizar_documentacion_dirigido.py](../../../admisiones/tests/test_actualizar_documentacion_dirigido.py)
  - doc org cambiado (Pendiente→Aceptado) → se refresca y el doc nativo se preserva;
    `tipo_convenio`/`estado` intactos;
  - sin cambios → no se recrea nada;
  - doc org quitado del legajo → se elimina solo ese, el nativo se preserva.
  Corren en la CI del PR (pytest local requiere Docker).
