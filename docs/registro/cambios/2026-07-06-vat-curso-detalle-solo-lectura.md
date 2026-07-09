# VAT: detalle de curso en modo solo lectura para perfiles de visualizacion

## Contexto

Los perfiles de solo visualizacion (Revisor de centro / provincial sin
edicion) no podian abrir el detalle de un Curso: en el panel de cursos del
centro la fila no ofrecia ninguna accion y el popup de edicion `#modalCurso`
estaba envuelto por completo en `{% if can_manage_centro %}`, por lo que ni
siquiera se renderizaba. Resultado: el usuario veia la fila del curso pero no
podia consultar sus datos (tipo, parametria de voucher, costo en creditos,
observaciones), que solo existian dentro del formulario de edicion.

La comision de curso ya resolvia este caso: tiene boton "Ver" (gateado por
`VAT.view_comisioncurso`) y un detalle donde todas las acciones se apagan via
`puede_gestionar_comision` (= `can_user_edit_centro`). Contactos, ubicaciones e
identificadores del centro tambien mostraban ya sus tablas al perfil de
visualizacion, ocultando solo los botones/modales de edicion.

## Cambio

Se agrega una vista de detalle **read-only** para el Curso, en lugar de reabrir
el modal de edicion:

- Nueva `CursoDetailView` (`VAT/views/curso.py`): `DetailView` GET-only cuyo
  queryset se acota a los centros legibles del usuario
  (`_readable_centros_ids`, incluye revisor). Expone `puede_editar_curso`
  (= `can_user_edit_centro` + perm `change_curso`) y `comisiones_count`. Al ser
  GET-only no habilita ningun vector de escritura.
- Nueva URL `vat_curso_detail` (`VAT/urls.py`): `vat/cursos/<int:pk>/`, gateada
  por `permissions_any_required(["VAT.view_curso"])`. No colisiona con
  `vat/cursos/comisiones/...` porque `<int:pk>` solo matchea digitos.
- Nuevo template `vat/curso/curso_detail.html`: muestra datos del curso,
  parametria de voucher (usa voucher, costo en creditos, vouchers habilitados) y
  cantidad de comisiones. El boton "Editar curso" solo aparece si
  `puede_editar_curso`.
- Panel de cursos (`partials/centro_cursos_panel.html`): la fila de curso ahora
  ofrece un boton "Ver" gateado solo por `perms.VAT.view_curso`, visible tambien
  para el perfil de solo visualizacion. Las acciones de gestion (crear comision,
  editar, borrar) siguen gateadas por `can_manage_centro`.

### Sin fuga en API/backend

- Los endpoints de edicion/accion de curso, comision, inscripcion, asistencia y
  horario ya filtran por `_scoped_centros_ids` /
  `_scoped_comisiones_curso_queryset`, ambos derivados de
  `filter_centros_queryset_for_management` (`include_revisores=False`). Un perfil
  de solo visualizacion recibe 404 ante cualquier POST de edicion, incluso si
  posee el permiso Django `change_*`. No fue necesario reforzar nada; se agrego
  un test que lo verifica.
- `CentroViewSet` y serializers de Centro usan `HasAPIKey` (server-to-server),
  no accesibles con la sesion del usuario.

## Validacion

Tests de regresion en `VAT/tests.py`:

- `test_curso_detail_revisor_ve_datos_en_solo_lectura`: el revisor abre el
  detalle (200), ve los datos y la parametria de voucher, sin enlace de edicion.
- `test_curso_detail_revisor_no_puede_editar_por_backend`: con `change_curso`
  otorgado, el POST a `vat_curso_update` devuelve 404 y el curso no se modifica.
- `test_cursos_panel_revisor_ve_boton_ver_sin_gestion`: el panel muestra el
  boton "Ver" al revisor y oculta la accion de crear comision.

Suite `-k "curso or centro or revisor or panel"`: 119 passed.
