# 2026-09-04 - El número de GDE de un documento se replica en el Informe Técnico

## Contexto
- Al aceptar un documento en `comedores/admisiones/tecnicos/editar/<pk>` se
  habilita un input para cargar su número de GDE. Ese número tiene que quedar
  también en el campo correspondiente del borrador del Informe Técnico,
  reemplazando el valor previo o cargándose por primera vez.
- Los formularios del informe **ya** hacían este prellenado, pero con nombres
  de documento hardcodeados y exactos, y dos de ellos nunca matcheaban:
  - `"Acta Solicitud de Subsidio"` — el nombre real del catálogo es
    `"Acta de Solicitud de Subsidio"`, así que `constancia_subsidios_dnsa`
    quedaba siempre vacío.
  - `"Nota de solicitud e Inclusión al Programa"` — solo existe con esa grafía
    para Personería Jurídica; en Eclesiástica y Organización Base es
    `"Nota de Solicitud e Inclusión al Programa"` (S mayúscula), y por eso
    `nota_gde_if` no se cargaba en esos convenios.
- Además el prellenado solo corría al construir el formulario: si el técnico
  editaba un GDE con el borrador ya guardado, el informe quedaba desfasado.

## Relación documento -> campo
| Documento | Campo del informe |
| --- | --- |
| Nota de (S/s)olicitud e Inclusión al Programa | `nota_gde_if` |
| Acta de Solicitud de Subsidio | `constancia_subsidios_dnsa` |
| Respuesta Memo PNUD | `constancia_subsidios_pnud` |
| Validación RENACOM | `validacion_registro_nacional` |
| Relevamiento Programa PAC / Programa Alimentar Comunidad (PAC-AC) | `if_relevamiento` (base) o `IF_relevamiento_territorial` (jurídico) |

## Cambios aplicados
- `admisiones/utils.py` es ahora la única fuente de verdad de esa relación:
  `GDE_DOCUMENTO_A_CAMPO_INFORME`, `normalizar_nombre_documento`,
  `campo_informe_para_numero_gde` y `numeros_gde_por_campo_de_informe`. Las
  claves están normalizadas (minúsculas, sin acentos, espacios colapsados), así
  que las variantes de grafía del catálogo matchean sin enumerarlas. El matcheo
  es por igualdad normalizada, no por substring, para que
  `"Memo PNUD"`, `"Inscripción RENACOM"` y `"Preinscripción RENACOM"` sigan sin
  mapear a nada.
- `admisiones_forms`: los cuatro bloques hardcodeados de cada formulario (base
  y jurídico) más `_if_relevamiento_a_pac` se reemplazan por un único
  `_prellenar_campos_gde(form, admision, tipo_informe)` que aplica la tabla
  compartida sobre los campos que el formulario expone. Se eliminó
  `_ultimo_numero_gde`, que quedó sin usos; su respaldo contra
  `NumeroGdeOrganizacion` está incorporado en
  `numeros_gde_por_campo_de_informe`.
- **Tercer bug, el que se veía en pantalla:** el prellenado escribía en
  `fields[campo].initial`, y Django ignora eso cuando el formulario está ligado
  a una instancia ya guardada (`form.initial` se arma desde la instancia y tiene
  prioridad). Es decir, el prellenado solo funcionaba para un informe que
  todavía no existía; al editar un informe ya creado el input seguía mostrando
  el valor viejo, incluso con el documento ya cargado. Ahora el valor se escribe
  también en `form.initial`, con `informe_admite_replica_gde` como guarda para
  no pisar un informe finalizado o validado. Con el formulario ligado a datos
  POST manda lo enviado por el usuario, así que enviar el formulario sigue
  guardando lo que está en pantalla.
- `InformeService.sincronizar_numero_gde_en_informe(archivo_admision)`: nuevo
  método que copia el GDE al borrador ya guardado. Reemplaza el valor previo, y
  si el documento queda sin GDE limpia el campo. Solo toca informes en borrador
  o recién iniciados (la misma ventana en la que `AdmisionService` permite
  modificar documentos), así que un informe finalizado o validado no se altera.
  Los documentos personalizados (sin `Documentacion`) no mapean a ningún campo.
- `AdmisionService.actualizar_numero_gde_ajax` invoca la sincronización después
  de guardar el documento y devuelve `campo_informe_actualizado`. Un fallo en la
  réplica se loguea pero no hace fracasar el guardado del GDE, que ya está
  hecho.
- `admisionesactualizarestado.js`: con ese dato, el input del informe que está
  en la misma página se actualiza sin recargar (`reflejarGDEEnInformeTecnico`),
  con un resaltado breve.

## Impacto esperado
- `constancia_subsidios_dnsa` y `nota_gde_if` empiezan a cargarse en los
  convenios donde antes quedaban vacíos por el nombre mal escrito.
- El borrador queda sincronizado tanto al crearse como al editar un GDE después.
- El documento es la fuente de verdad mientras el informe está en borrador: una
  edición manual del campo se sobrescribe si después se toca el GDE del
  documento.

## Pendiente conocido
- `validacion_registro_nacional` no está declarado en `InformeTecnicoBaseForm`
  (solo en el jurídico), así que para Organización Base ese campo no se muestra
  aunque el documento "Validación RENACOM" exista en el catálogo de ese
  convenio. Queda fuera de este cambio porque implica decidir si el campo
  corresponde al informe base.

## Validación
- `tests/test_admisiones_gde_informe_sync_db.py` (nuevo, 22 tests): un caso por
  documento mapeado, el relevamiento según tipo de informe, reemplazo de valor
  previo, limpieza al borrar el GDE, informe finalizado intacto, documento sin
  mapeo, documento personalizado, sin informe, y el flujo real por el endpoint
  AJAX verificando `campo_informe_actualizado` y el valor persistido. Incluye
  tres casos con el formulario real (`InformeTecnicoBaseForm`) que cubren el
  bug de `form.initial`: el input muestra el GDE del documento sobre un
  borrador guardado vacío, un informe finalizado conserva lo suyo, y con datos
  POST manda lo enviado.
- `tests/test_admisiones_forms_unit.py`: los tests de `_if_relevamiento_a_pac` y
  `_ultimo_numero_gde` se reemplazaron por tests de `_prellenar_campos_gde`,
  con uno específico de regresión sobre `form.initial`.
- Reproducción manual contra la admisión 4 de la base de desarrollo: con los
  documentos 43 y 44 con GDE cargado y los campos del informe vacíos en la
  base, la página ahora renderiza `value="nenu"` y `value="12b"`.
- Contraste del mapeo contra el catálogo real de las tres personerías, con
  casos negativos.
- `pytest -n auto` completo: 4680 passed. Queda un único fallo,
  `test_csv_export_architecture`, verificado como preexistente con `git stash`.
- `black` limpio; `pylint` sin hallazgos nuevos (los 4 restantes son previos).

## Riesgos y rollback
- Riesgo principal: la tabla se indexa por nombre de documento, así que si en el
  catálogo se renombra un documento la réplica deja de aplicarse en silencio.
  Un mapeo por ID de `Documentacion` sería más robusto pero hay una fila por
  cada tipo de convenio.
- Rollback: revertir el commit. No hay migraciones; los valores ya replicados en
  informes quedan como están.
