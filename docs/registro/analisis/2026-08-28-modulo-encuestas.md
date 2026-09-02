# Análisis funcional: Módulo de Encuestas

## Fecha
2026-08-28 (análisis) — implementación completada el 2026-08-29

## Estado: implementado
Las 8 fases del roadmap (más abajo) están implementadas y verificadas en la rama
`feature/modulo-encuestas`: 168 tests propios de `encuestas/` en verde (145 del
MVP original + 23 del sistema de puntaje agregado el 2026-08-31, ver regla de
negocio 18), más una corrida completa del proyecto (`pytest -n auto`, ~4360
tests) sin regresiones nuevas — los únicos fallos de esa corrida (16, en
`centrodeinfancia/`) son preexistentes y no relacionados, confirmado
corriéndolos contra `development` con los cambios de este módulo revertidos
vía `git stash`. Ver "Estado final de la implementación" al pie de este
documento para el resumen de desvíos respecto de lo planeado acá y hallazgos
del desarrollo.

## Objetivo
Crear un nuevo módulo (app `encuestas/`) que permita a un rol específico ("Gestor de Encuestas") generar encuestas dirigidas a usuarios logueados de SISOC, con preguntas de distinto tipo, lógica condicional simple, segmentación de destinatarios y programación recurrente, para relevar feedback periódico. Los usuarios responden dentro del sistema mediante un modal que aparece al iniciar sesión.

## Situación actual
No existe módulo de encuestas en SISOC. El antecedente más cercano es `comunicados/`, que permite emitir comunicaciones dirigidas a comedores/organizaciones (con adjuntos y mailing masivo), pero no soporta preguntas estructuradas, respuestas, ni lógica condicional. Tampoco existe hoy ningún mecanismo de scheduler/cron real en el repo: las tareas periódicas se resuelven con un patrón de *management command* corriendo en loop dentro de un servicio propio de `docker-compose.yml` (ver `ocr/management/commands/process_ocr_jobs.py`, `process_mailing_jobs.py`, etc.).

Además, hoy conviven dos modelos "Programa" no unificados (`core.Programa`, vinculado a `ciudadanos` vía `CiudadanoPrograma`, y `comedores.Programas`, que clasifica comedores), y ninguno de los dos se relaciona con el usuario logueado. El alcance de un usuario en el sistema se modela hoy por provincia/dupla (`users.Profile`), no por programa.

## Ubicación funcional
- Nueva app de dominio `encuestas/`, integrada como ítem dentro de la sección de menú ya existente "Administración del sistema" (ver detalle en "Ubicación en el menú" más abajo), no como sección propia de primer nivel.
- Un modal/pop-up transversal, disparado tras el login, que se muestra en cualquier pantalla del sistema mientras el usuario tenga rondas de encuesta pendientes.

## Componentes principales

### Modelo (implementado — `encuestas/models.py`)
- `Encuesta`
  - `titulo`, `descripcion`
  - `estado` (`EstadoEncuesta`: `borrador` / `publicada` / `cerrada` / `archivada`, análogo a `comunicados.EstadoComunicado`)
  - `es_anonima` (bool)
  - `es_obligatoria` (bool)
  - `intervalo_recordatorio_dias` (entero, nullable; obligatorio si `es_obligatoria=False` — validado en `Encuesta.clean()`; define cada cuánto reaparece tras "responder más tarde")
  - `es_recurrente` (bool) + `intervalo_recurrencia_dias` (entero, opcional): no hay un catálogo fijo de frecuencias (diaria/semanal/mensual); el Gestor define libremente cada cuántos días se abre una nueva ronda, o deja la encuesta como de única vez (`es_recurrente=False`)
  - `duracion_ronda_dias` (cuánto dura abierta cada ronda antes del cierre automático)
  - `version` (entero) y `version_de` (FK a sí misma, nullable, `on_delete=PROTECT`) — para versionado al editar con respuestas ya recibidas; `UniqueConstraint(version_de, version)` evita duplicar versiones
  - `usuario_creador`, `usuario_ultima_modificacion` (ambos `on_delete=PROTECT`, mismo patrón que `comunicados.Comunicado`), `fecha_creacion`, `fecha_ultima_modificacion`
  - `Meta.permissions = [("ver_resultados", ...)]`
- `Pregunta`
  - `encuesta` (FK, `CASCADE`), `texto`, `orden`
  - `tipo` (`TipoPregunta`: texto_corto / texto_largo / opcion_unica / opcion_multiple / escala / si_no / numerico / fecha)
  - `obligatoria` (bool, independiente del flag general de la encuesta)
  - Condición de visibilidad implementada como **tres campos planos**, no un objeto anidado: `pregunta_condicion` (FK a sí misma, nullable, `SET_NULL`) + `operador_condicion` (`OperadorCondicion`: igual/distinto) + `valor_condicion` (texto libre) — muestra/oculta la pregunta según la respuesta de otra pregunta anterior. `Pregunta.clean()` valida que la referencia sea de la misma encuesta y que los tres campos vayan juntos.
  - `pondera` (bool, default `False`) + `puntaje_si` / `puntaje_no` (enteros, nullable, solo para `tipo=si_no`) — ver "Puntaje por pregunta" en Reglas de negocio. `Pregunta.clean()` rechaza `pondera=True` en tipos sin un conjunto fijo de valores (texto/numérico/fecha) y rechaza `puntaje_si`/`puntaje_no` fuera de `si_no`.
- `OpcionPregunta`
  - `pregunta` (FK, `CASCADE`), `texto`, `valor`, `orden`, `puntaje` (entero, default `0`; solo se usa si `pregunta.pondera=True`)
- `SegmentacionEncuesta`
  - `encuesta` (`OneToOneField`, `CASCADE`), `tipo` (`TipoSegmentacion`: `todos_los_usuarios` / `listado_documentos`; segmentación por "Programa" quedó pospuesta, ver Fuera de alcance)
  - `archivo_listado` (FileField, opcional, para carga por Excel/CSV, con validadores de extensión/tamaño)
- `SegmentacionDestinatario`
  - `segmentacion` (FK, `CASCADE`), `tipo_documento` (`TipoDocumento`: DNI/CUIT/CUIL), `numero_documento` — `UniqueConstraint` por los tres campos
- `RondaEncuesta`
  - `encuesta` (FK, `on_delete=PROTECT` — protege el historial de rondas), `numero_ronda`, `fecha_apertura`, `fecha_cierre_programada`, `fecha_cierre_real` (nullable), `estado` (`EstadoRonda`: abierta/cerrada), `cerrada_manualmente` (bool) — `UniqueConstraint(encuesta, numero_ronda)`
- `RespuestaRonda`
  - `ronda` (FK, `on_delete=PROTECT`), `usuario` (FK, `PROTECT` — **siempre se registra**, incluso en encuestas anónimas, ver regla de negocio 1), `fecha_respuesta`, `completa` (bool) — `UniqueConstraint(ronda, usuario)`
  - No se persisten respuestas parciales: `registrar_respuesta()` corre dentro de una `transaction.atomic()`; si una pregunta obligatoria falla la validación a mitad de camino, no queda ni `RespuestaRonda` ni `RespuestaPregunta` a medio completar
- `RespuestaPregunta`
  - `respuesta_ronda` (FK, `CASCADE`), `pregunta` (FK, `PROTECT`), `valor_texto` / `valor_numero` (`DecimalField`) / `valor_fecha` / `opciones_seleccionadas` (M2M a `OpcionPregunta`) — `UniqueConstraint(respuesta_ronda, pregunta)`
- `RecordatorioUsuario`
  - `ronda` (FK, `CASCADE`), `usuario` (FK, `CASCADE`), `fecha_proximo_aviso` (soporta el "responder más tarde") — `UniqueConstraint(ronda, usuario)`

### Ubicación en el menú
- Se integra como un nuevo ítem dentro de la sección ya existente **"Administración del sistema"** (`templates/includes/sidebar/opciones.html:68-122`), que hoy agrupa Usuarios, Grupos, Programas, Auditoría, Papelera y Parametrías de Voucher. No se crea una sección de nivel superior nueva ni una pestaña dentro de otro módulo.
- El bloque completo de esa sección ya está condicionado a `request.user|has_any_perm:"..."`; el nuevo `<li>` de Encuestas se agrega dentro de su `<ul class="nav nav-treeview">`, gateado con `{% if request.user|has_any_perm:"encuestas.view_encuesta,encuestas.ver_resultados" %}` (mismo patrón que usan `Grupos` y `Auditoría` en ese mismo bloque), siguiendo el filtro `has_perm_code`/`has_any_perm` de `core/templatetags/custom_filters.py` (basados en `core/permissions/registry.py`).
- Debe agregarse también la condición de que `request.user|has_any_perm:"...encuestas..."` participe del `if` general que envuelve toda la sección "Administración del sistema" (línea 68), para que la sección se muestre aunque el usuario solo tenga permisos de Encuestas y ninguno de Usuarios/Grupos/Auditoría.

### Roles y permisos
- Grupo nuevo `Gestor de Encuestas`, definido como `BootstrapGroupSeed` en `users/bootstrap/groups_seed.py` (mismo mecanismo usado para `Comedor Insumos Gestión`/`Comedor Insumos Consulta`): incluye los permisos default `add`/`change`/`delete`/`view` de Django sobre `Encuesta`, `Pregunta`, `OpcionPregunta`, `SegmentacionEncuesta`, `RondaEncuesta` (crear, editar, publicar, cerrar manualmente).
- Permiso independiente `encuestas.ver_resultados`: **no es CRUD**, se declara en `Meta.permissions` del modelo `Encuesta` (mismo patrón que `celiaquia.Expediente` con `view_cupo_dashboard`/`view_reporte_provincias` en `celiaquia/models.py`). Habilita el acceso a resultados/dashboard/exportación.
- Grupo nuevo `Encuestas Resultados` (nombre definitivo, siguiendo el patrón `<Módulo> <Rol>` usado en `Comedor Insumos Gestión`/`Comedor Insumos Consulta`), también como `BootstrapGroupSeed`, con `encuestas.view_encuesta` (default, para poder llegar al listado) + `encuestas.ver_resultados` (custom) — independiente del grupo `Gestor de Encuestas`, pudiendo asignarse a las mismas personas o a un equipo distinto.
- Si en algún momento se necesita otorgar `ver_resultados` a usuarios que ya existen al momento de introducir el permiso (por ejemplo, dar de alta el permiso después de que el módulo ya está en producción), se resuelve con una data migration que crea el `Permission` vía `get_or_create` y lo asigna a los grupos correspondientes — mismo patrón que `celiaquia/migrations/0006_seed_permisos_dashboard_reporte.py`. Para el alta inicial del módulo no hace falta: los permisos de `Meta.permissions` se crean solos en `post_migrate` y se asignan a los grupos vía el bootstrap seed.

### Vistas / URL (implementadas — `encuestas/urls.py`)
- `encuestas/` → listado, accesible tanto a `Gestor de Encuestas` como a `Encuestas Resultados`; los botones de alta/edición/publicación/cierre solo se muestran y habilitan para quien tenga los permisos de gestión, quien solo tiene `ver_resultados` ve el mismo listado pero únicamente con acceso al link de resultados de cada encuesta
- `encuestas/crear/` → alta ("Generar encuesta"), incluye el editor dinámico de preguntas
- `encuestas/<pk>/editar/` → edición (genera nueva versión si ya tiene respuestas; **bloqueada por completo si hay una ronda abierta**, regla 17)
- `encuestas/<pk>/publicar/`
- `encuestas/<pk>/rondas/<ronda_pk>/cerrar/` → cierre manual anticipado
- `encuestas/<pk>/resultados/` → dashboard agregado, en vivo, con selector de ronda (solo `ver_resultados`)
- `encuestas/<pk>/resultados/rondas/<ronda_pk>/exportar/?formato=csv|xlsx` → export
- `encuestas/responder/<ronda_pk>/` → recibe el POST del modal de respuesta
- `encuestas/responder/<ronda_pk>/mas-tarde/` → snooze
- `encuestas/<pk>/segmentacion/` → gestión de destinatarios (Fase 4), **página separada del formulario de edición a propósito**: la segmentación se modifica en caliente incluso con una ronda abierta (regla 12), mientras que editar preguntas/config sí está bloqueado en ese caso (regla 17) — mezclarlas habría bloqueado algo que la propia regla de negocio permite
- `encuestas/<pk>/segmentacion/tipo/` → cambia `todos_los_usuarios`/`listado_documentos` y/o reemplaza el listado completo por archivo
- `encuestas/<pk>/segmentacion/agregar/` → alta individual de un destinatario (tipo + número, sin buscador por nombre — ver "Fuera de alcance")
- `encuestas/<pk>/segmentacion/<destinatario_pk>/quitar/` → baja individual

### UI / comportamiento
- Ítem "Encuestas" dentro de "Administración del sistema", visible según permisos (`Gestor de Encuestas` y/o `ver_resultados`).
- Editor de preguntas: alta dinámica de preguntas, tipo seleccionable, opciones cuando corresponde, flag "obligatoria" por pregunta, selector de condición "mostrar si pregunta X = valor Y".
- Modal transversal post-login:
  - Si hay varias rondas pendientes para el usuario, se muestran en cola, una por vez, ordenadas por fecha de vencimiento de ronda más próxima primero.
  - Encuesta obligatoria: modal sin botón de cierre ni "responder más tarde"; bloquea la navegación hasta completar.
  - Encuesta no obligatoria: botones "Responder" y "Responder más tarde"; al elegir "más tarde" se agenda `RecordatorioUsuario.fecha_proximo_aviso` según `intervalo_recordatorio` configurado por quien creó la encuesta.
  - No hay aviso por email: la única notificación es este modal dentro del sistema.
  - Sin límite de tiempo para completar una vez abierto el modal; no se guarda avance parcial (ver `RespuestaRonda` arriba).
  - No hay una sección de "mis encuestas respondidas": una vez completada, la encuesta no vuelve a ser accesible para el usuario que la respondió.

## Reglas de negocio
1. **Anonimato vs. obligatoriedad**: una encuesta anónima registra el *hecho* de que un usuario respondió una ronda (para poder desbloquearlo y no volver a mostrarle la encuesta), pero el *contenido* de sus respuestas nunca se vincula a su identidad en reportes, exportaciones ni pantallas de resultados.
2. Cada pregunta tiene su propio flag obligatoria/opcional, independiente del flag general de la encuesta.
3. La lógica condicional solo permite mostrar/ocultar preguntas individuales según la respuesta de una pregunta anterior (no hay saltos de sección ni condiciones combinadas con AND/OR).
4. Editar una encuesta que ya tiene respuestas genera una nueva versión; las respuestas emitidas quedan asociadas a la versión vigente al momento de responder.
5. La recurrencia genera una **ronda independiente por período** (no se resetea ni se reabre la misma); esto permite comparar resultados entre rondas de una misma encuesta a lo largo del tiempo.
6. Una ronda se cierra automáticamente al llegar su fecha de cierre programada, o manualmente antes de tiempo por el Gestor de Encuestas.
7. Si la encuesta es obligatoria, bloquea el uso del sistema para el usuario destinatario hasta que complete la ronda vigente.
8. Si no es obligatoria, el intervalo de reaparición tras "responder más tarde" lo define quien crea la encuesta (no es un valor fijo global).
9. La segmentación de destinatarios admite "todos los usuarios logueados" o un listado explícito de DNI/CUIT/CUIL, cargado por archivo (Excel/CSV) o mediante buscador/selector interno. La segmentación por "Programa" queda **pospuesta a fase 2** (ver Fuera de alcance).
10. El permiso para ver resultados (`encuestas.ver_resultados`) es independiente del permiso para gestionar encuestas.
11. Los resultados son visibles en vivo mientras la ronda está abierta, sin necesidad de esperar su cierre.
12. Si el listado de segmentación de una encuesta se modifica mientras la ronda está abierta, el cambio se aplica **en caliente**: agregar o quitar un documento agrega o retira de inmediato a esa persona de la ronda en curso.
13. No hay un catálogo fijo de frecuencias de recurrencia: una encuesta puede ser de única vez o recurrente con un intervalo en días definido libremente por quien la crea (no valores predefinidos tipo "semanal"/"mensual").
14. Toda alta, edición, publicación y cierre de encuesta queda registrada en el módulo `audittrail` ya existente en el repo.
15. No se conserva historial de respuestas navegable por el propio usuario que respondió, ni existe funcionalidad de duplicar una encuesta como plantilla en el MVP.
16. No hay política de borrado ni archivado automático: encuestas y respuestas se conservan indefinidamente.
17. No se puede editar una encuesta (generar nueva versión) mientras tenga una ronda abierta: el Gestor debe cerrarla (manual o automáticamente) antes de poder crear la siguiente versión.
18. **Puntaje por pregunta** (agregado 2026-08-31, ver `encuestas/services_resultados.py`): el Gestor puede marcar una pregunta como que "pondera" para un puntaje total, únicamente si es de un tipo con un conjunto fijo de valores posibles (`Sí/No`, `Opción única`, `Opción múltiple`, `Escala`) — texto libre, numérico y fecha no participan del puntaje.
    - El puntaje se define **por opción de respuesta**, no por pregunta completa: cada opción (o cada una de "Sí"/"No") tiene su propio valor en puntos, asignado por el Gestor. En preguntas de escala no hay valor configurable: el número que responde la persona (1 a 10) es directamente su puntaje en esa pregunta.
    - Puntaje obtenido por pregunta: opción única → puntos de la opción elegida; opción múltiple → suma de puntos de todas las opciones marcadas; Sí/No → puntos de la opción respondida; escala → el valor numérico ingresado.
    - Puntaje máximo posible por pregunta (para calcular el total): opción única y Sí/No → el mayor puntaje entre sus opciones (se elige una sola); opción múltiple → suma de puntos de **todas** sus opciones; escala → 10 fijo.
    - El **total posible de una encuesta es fijo**: suma los puntos máximos de todas las preguntas que ponderan, aunque a una persona en particular no le hayan aparecido algunas por la lógica condicional (regla 3) — no se ajusta por persona.
    - El puntaje de cada respuesta se muestra **solo en el dashboard de Resultados** (sección "Puntaje por respuesta", ordenada de mayor a menor) y en la exportación CSV/Excel (columnas "Puntaje obtenido"/"Puntaje total") — nunca se le muestra a quien respondió. Igual que el resto de Resultados, respeta la regla 1: en encuestas anónimas no se expone qué usuario obtuvo qué puntaje, solo el valor.
    - Si ninguna pregunta de la encuesta pondera, no se calcula ni se muestra nada de puntaje (sin sección vacía ni columnas en 0).

## Dependencias y servicios
- **Scheduler**: se reutiliza el patrón existente de *management command* + servicio propio en `docker-compose.yml` (como `ocr_worker` o el worker de `process_mailing_jobs.py`), agregando un chequeo periódico de fechas de rondas (apertura, cierre y evaluación de `intervalo_recurrencia_dias`). No se introduce Celery Beat.
- **Carga de listados de segmentación**: reutilizar el patrón de archivo ya usado en `comunicados.MailingJob` (upload + validación de filas) para la carga por Excel/CSV. Los cambios al listado deben poder aplicarse en caliente sobre una ronda abierta (alta/baja de destinatario sin esperar al próximo ciclo).
- **Auditoría**: instrumentar altas/ediciones/publicaciones/cierres de `Encuesta` y `RondaEncuesta` contra el módulo `audittrail` existente, siguiendo el mismo mecanismo que usan otras entidades ya auditadas del repo.
- **Servicio** `encuestas/services.py` (según convención del repo, lógica de negocio fuera de views/models): `crear_encuesta`, `nueva_version`, `publicar`, `abrir_ronda`, `cerrar_ronda`, `registrar_respuesta`, `get_rondas_pendientes(usuario)`, `snooze_ronda(usuario, ronda)`, `actualizar_segmentacion(encuesta, listado)`.
- **Puntaje**: `encuestas/services_resultados.py` agrega `encuesta_pondera(encuesta)`, `puntaje_total_posible(encuesta)` y `get_puntajes_ronda(ronda)` — cálculo puro a partir de `Pregunta.pondera`/`puntaje_si`/`puntaje_no` y `OpcionPregunta.puntaje`, sin persistir el puntaje en ningún lado (se recalcula siempre en el momento).

## Criterios de aceptación
1. Un usuario con el rol `Gestor de Encuestas` puede crear una encuesta desde "Generar encuesta", agregar preguntas de todos los tipos soportados, configurar condiciones de visibilidad, anonimato, obligatoriedad, recurrencia y segmentación.
2. Al publicar una encuesta, se genera la primera `RondaEncuesta` según la segmentación configurada.
3. Un usuario incluido en la segmentación ve el modal al loguearse; si la encuesta es obligatoria no puede cerrarlo sin responder; si no lo es, puede posponerlo y vuelve a aparecer según el intervalo configurado.
4. Al completar una respuesta, si la encuesta es anónima, el sistema registra que el usuario respondió pero ningún reporte muestra el contenido de su respuesta vinculado a su identidad.
5. Al vencer la fecha de cierre programada, la ronda deja de aceptar respuestas automáticamente; el Gestor también puede cerrarla manualmente antes.
6. Una encuesta recurrente genera una nueva ronda independiente en cada ciclo, permitiendo comparar resultados entre rondas.
7. Solo quienes tienen el permiso `encuestas.ver_resultados` acceden al dashboard de resultados y a la exportación, en vivo mientras la ronda está abierta.
8. Editar una encuesta con respuestas ya recibidas crea una nueva versión sin alterar las respuestas históricas.
9. Al modificar el listado de segmentación de una encuesta con una ronda abierta, el destinatario agregado/quitado se refleja de inmediato en esa ronda (no solo en la siguiente).
10. La exportación de resultados incluye, además de las respuestas, metadatos de ronda, fecha de respuesta y versión de encuesta.
11. Toda acción de gestión sobre una encuesta (alta, edición, publicación, cierre) genera un registro en `audittrail`.
12. Si un usuario tiene más de una ronda pendiente, el modal las presenta en cola ordenadas por fecha de vencimiento más próxima.
13. Un usuario con el permiso `encuestas.ver_resultados` (sin ser Gestor) puede acceder al listado de encuestas y a los resultados de cada una, sin ver ni poder usar acciones de alta/edición/publicación/cierre.
14. El botón de editar una encuesta permanece deshabilitado (o la acción es rechazada) mientras tenga una ronda abierta; solo vuelve a estar disponible tras cerrarla.
15. Si el Gestor marca al menos una pregunta como "pondera", el dashboard de Resultados muestra el puntaje obtenido por cada respuesta sobre un total fijo, ordenado de mayor a menor; si ninguna pregunta pondera, esa sección no aparece.

## Casos de uso
### Caso 1: encuesta obligatoria segmentada por listado
El Gestor de Encuestas crea una encuesta de satisfacción, marca "obligatoria", sube un Excel con los DNI destinatarios y publica. Al loguearse, cada usuario de esa lista ve el modal bloqueante y no puede seguir usando SISOC hasta responder.

### Caso 2: encuesta no obligatoria con recordatorio
El Gestor crea una encuesta abierta a todos los usuarios, no obligatoria, con recordatorio cada 3 días. Un usuario elige "responder más tarde"; el modal no vuelve a aparecer hasta pasado ese intervalo.

### Caso 3: encuesta anónima recurrente
El Gestor crea una encuesta de clima laboral, anónima, recurrente con un intervalo de 30 días. Cada ciclo se abre una nueva ronda; quienes ya respondieron esa ronda no vuelven a ver el modal, pero nadie (ni el Gestor) puede ver qué respondió cada persona en particular. El equipo con permiso de resultados compara los agregados entre rondas.

### Caso 4: lógica condicional
Una pregunta de opción única ("¿Usás el módulo X?") tiene una pregunta de seguimiento ("¿Qué mejorarías?") configurada para mostrarse solo si la respuesta fue "Sí".

## Recomendaciones técnicas

### Estructura de la app (plantilla: `insumos/`)
`insumos/` es la app de dominio más reciente y de tamaño comparable al MVP de encuestas; se recomienda tomarla como plantilla de estructura en vez de apps más viejas/grandes como `duplas/`:
```
encuestas/
    __init__.py
    admin.py
    apps.py
    forms.py
    migrations/
        0001_initial.py
    models.py
    services.py
    urls.py
    validators.py
    views.py
    tests/
        test_encuestas_permisos.py
        ...
```
- `Meta.permissions` de `ver_resultados` va en `models.py`, sobre `Encuesta`.
- Los grupos `Gestor de Encuestas` / `Encuestas Resultados` se agregan a `users/bootstrap/groups_seed.py` (no como fixture ni migración de datos, salvo el caso de alta tardía de permisos ya mencionado).
- El ítem de menú se agrega en `templates/includes/sidebar/opciones.html`, dentro de la sección "Administración del sistema".

### Middleware y bloqueo por encuesta obligatoria
- Corrección respecto de una revisión anterior de este documento: **sí hay precedente exacto** en el repo para este tipo de bloqueo. `users/middleware.py` ya implementa dos middlewares con la misma necesidad — interceptar cualquier request de un usuario autenticado y redirigirlo hasta que cumpla una condición pendiente:
  - `FirstLoginPasswordChangeMiddleware`: si `profile.must_change_password`, redirige a `password_change_required` salvo en rutas exentas.
  - `ProfileConfirmationMiddleware`: si `needs_profile_confirmation(user)`, redirige a `confirmar_datos_personales` salvo en rutas exentas. Corre después del anterior a propósito, con una nota explícita en su docstring sobre el orden para evitar loops entre ambos middlewares.
  - Ambos comparten `COMMON_EXEMPT_PATHS` / `COMMON_EXEMPT_PREFIXES` (logout, estáticos, media) y un helper `_is_login_path`.
- **Recomendación de diseño**: implementar `encuestas/middleware.py` con un `EncuestaObligatoriaMiddleware` que siga exactamente este mismo patrón (mismo criterio de exención de rutas, mismo estilo de `__call__`), y agregarlo al stack de `config/settings.py` **después** de `ProfileConfirmationMiddleware`. El orden importa: un usuario con contraseña o datos personales pendientes debe resolver eso primero; recién después se le exige la encuesta obligatoria. Esto evita reinventar un mecanismo de bloqueo transversal nuevo y mantiene el mismo estilo que ya audita/revisa el equipo.
- Rutas a eximir además de las comunes: las propias de `encuestas/responder/...` (para poder completarla) y `encuestas/responder/.../mas-tarde/` (no aplica si es obligatoria, pero la ruta de responder sí debe quedar exenta del propio bloqueo que dispara).

### Componentes de UI a reutilizar (no reinventar)
Stack real del proyecto (`templates/includes/base.html`, `docs/ia/STYLE_GUIDE.md`): Bootstrap 5 + tema AdminLTE, Font Awesome 5 + Bootstrap Icons, ApexCharts, Select2, DataTables 1.11.5, jquery-confirm, toastr. CSS propio en `static/custom/css/` (`poncho.css`, `poncho_listados.css`). No hay `django-crispy-forms` en uso real ni formsets de Django pese a existir el `{% load %}` en `base.html`; los formularios se arman a mano.

- **Modal de encuesta pendiente**: reusar `templates/components/modal.html`, un include parametrizable (`modal_id`, `title`, `content`/`form`, `buttons`, `size`, `centered`, `trigger_button`) sobre Bootstrap 5 estándar. Pasarle como `form` el formulario dinámico con las preguntas visibles según la condición configurada.
- **Editor de preguntas y opciones (alta/baja dinámica)**: no usar formsets de Django; seguir el patrón ya usado en el repo de `<template>` HTML + clonado por JS: `templates/components/search_bar.html` (bloque `#poncho-filter-row-template`) y su JS en `static/custom/js/advanced_filters.js` (`rowTemplate.content.cloneNode(true)`), o el patrón de `static/custom/js/comunicadosForm.js` para agregar/quitar bloques con badges removibles. Mismo mecanismo sirve para agregar preguntas, opciones por pregunta, y el selector de "mostrar si pregunta X = valor Y".
- **Listado de encuestas**: reusar `templates/components/search_bar.html` en modo `filters_mode=True` (filtros combinables) o `ajax_search_mode=True` (paginación server-side vía fetch), tal como lo usa `comunicados/templates/comunicados/comunicado_list.html` + `ComunicadoListView`.
- **Buscador de destinatarios** (alternativa a subir archivo, para segmentación por DNI/CUIT/CUIL): mismo componente `search_bar.html` en modo `ajax_search_mode=True`.
- **Dashboard de resultados**: reusar ApexCharts (ya cargado globalmente en `base.html`) y las tarjetas KPI `.custom-card.card-violet/card-red/card-green` de `dashboard/templates/dashboard.html` (líneas 51-80) para métricas agregadas por pregunta (ej. % de respuestas, promedio de escala, distribución de opciones).
- **Exportación CSV**: reusar `core/services/csv_export.py` (`build_csv_response(filename)`, ya maneja BOM UTF-8 y `Content-Disposition`), igual que el botón `.btn-export-csv` de `search_bar.html`.
- **Exportación Excel**: reusar el patrón `openpyxl` de `VAT/services/nomina_export.py` (o `celiaquia/services/padron_final_service/impl.py`) para generar el archivo con metadatos de ronda/fecha/versión.
- **Ítem de menú**: agregarlo directamente en `templates/includes/sidebar/opciones.html`, sin crear un template de sidebar propio.

## Fuera de alcance de este análisis (pospuesto a fase 2)
- Segmentación de destinatarios por "Programa": hoy conviven `core.Programa` y `comedores.Programas`, no unificados y sin relación con el usuario. Para el MVP la segmentación se limita a "todos los usuarios" o "listado de DNI/CUIT/CUIL". **Nuevo dato**: `core.Programa` ya es administrado desde la propia sección "Administración del sistema" del menú (`programa_listar`, junto a Usuarios/Grupos/Auditoría) y tiene FK a `organizaciones.Organizacion`, por lo que es el candidato más natural para reusar en fase 2 en vez de crear un catálogo nuevo — a confirmar en el análisis aparte, evaluando cómo resolver la relación Usuario↔Programa que hoy no existe.
- Notificación por email de nuevas rondas (el MVP solo usa el modal dentro del sistema).
- Historial de encuestas ya respondidas consultable por el propio usuario.
- Duplicar una encuesta existente como plantilla.
- Guardado de respuestas parciales/borrador dentro de una misma ronda.
- Política de archivado o borrado de encuestas y respuestas antiguas (por ahora se conservan indefinidamente).
- Diseño visual/UX de detalle (copies, microcopy, ilustraciones): la estructura de componentes a reusar ya quedó definida en "Componentes de UI a reutilizar" más abajo; lo que queda fuera de alcance es el detalle fino de redacción y estilo visual específico.

## Decisiones ya resueltas (no requieren más definición funcional)
- **Scheduler**: se reutiliza el patrón worker + servicio `docker-compose` existente (no se introduce Celery).
- **Cola de pendientes**: rondas pendientes en cola, una por vez, ordenadas por fecha de vencimiento más próxima.
- **Cambios de segmentación en ronda abierta**: se aplican en caliente, no solo a la siguiente ronda.
- **Recurrencia**: sin catálogo fijo de frecuencias; intervalo en días configurable libremente por encuesta, o de única vez.
- **Progreso a medias**: sin límite de tiempo, pero sin guardado de borrador (se retoma desde el principio).
- **Auditoría**: toda acción de gestión queda registrada en `audittrail`.
- **Exportación**: incluye metadatos de ronda, fecha de respuesta y versión de encuesta.
- **Retención**: se conserva todo indefinidamente, sin borrado automático.
- **Edición con ronda abierta**: no se permite generar una nueva versión mientras la ronda vigente sigue abierta; hay que cerrarla primero.
- **Middleware de bloqueo obligatorio**: reutiliza el patrón exacto de `FirstLoginPasswordChangeMiddleware`/`ProfileConfirmationMiddleware` (`users/middleware.py`), insertado después de ambos en el stack de `config/settings.py`.
- **Acceso al listado para el grupo de resultados**: el grupo `Encuestas Resultados` incluye también `encuestas.view_encuesta` (no solo el permiso custom) para poder llegar al listado y de ahí a los resultados.

No quedan preguntas funcionales abiertas para avanzar con el diseño técnico del MVP; los puntos de la sección "Fuera de alcance" son decisiones explícitamente diferidas, no bloqueantes.

## Roadmap de implementación

Trabajo en rama `feature/modulo-encuestas` (creada desde `development`). Fases pensadas para poder mergear en incrementos revisables (evitar un PR gigante mezclando modelo + UI + scheduler), cada una con su propio criterio de salida.

### Fase 0 — Setup
- Crear la app `encuestas/` (`manage.py startapp`), registrar en `INSTALLED_APPS` (`config/settings.py`).
- Armar el esqueleto de archivos siguiendo `insumos/` como plantilla (`admin.py`, `forms.py`, `models.py`, `services.py`, `urls.py`, `validators.py`, `views.py`, `tests/`).
- **Salida**: app instalada, `pytest` corre sin errores sobre el esqueleto vacío.

### Fase 1 — Modelo de datos y permisos base
- Implementar los modelos definidos en "Componentes principales": `Encuesta` (con `Meta.permissions` de `ver_resultados`), `Pregunta`, `OpcionPregunta`, `SegmentacionEncuesta`, `SegmentacionDestinatario`, `RondaEncuesta`, `RespuestaRonda`, `RespuestaPregunta`, `RecordatorioUsuario`.
- Migración inicial + registro en `admin.py` (habilita gestión manual temprana para QA antes de tener UI propia).
- Agregar `BootstrapGroupSeed("Gestor de Encuestas", (...))` y `BootstrapGroupSeed("Encuestas Resultados", (...))` en `users/bootstrap/groups_seed.py`.
- Tests de permisos por grupo, siguiendo `insumos/tests/test_insumos_permisos.py` como plantilla.
- **Salida**: modelos migrados, grupos bootstrap creados, tests de permisos en verde.

### Fase 2 — Backend de gestión (CRUD del Gestor)
- `services.py`: `crear_encuesta`, `nueva_version` (bloqueada si hay ronda abierta — regla 17), `publicar`, `abrir_ronda`, `cerrar_ronda`, `actualizar_segmentacion`.
- `forms.py` + `views.py` + `urls.py`: listado, alta, edición, publicar, cerrar ronda manual — sin UI final todavía (puede ir con templates mínimos).
- `validators.py`: validación del archivo de listado (Excel/CSV), reusando el criterio de `comunicados.MailingJob`.
- Instrumentar `audittrail` en alta/edición/publicación/cierre.
- **Salida**: un Gestor puede crear, versionar, publicar y cerrar una encuesta de punta a punta vía backend, con tests de servicios.

### Fase 3 — UI de gestión (reusando componentes)
- Listado: `templates/components/search_bar.html` en `filters_mode`, igual que `comunicado_list.html`.
- Editor de preguntas/opciones: patrón `<template>` + clonado JS (`advanced_filters.js`/`comunicadosForm.js`) para alta/baja dinámica, incluyendo el selector de condición de visibilidad por pregunta.
- Ítem de menú en `templates/includes/sidebar/opciones.html`, dentro de "Administración del sistema", gateado por `has_any_perm`.
- **Salida**: el Gestor arma una encuesta completa desde la UI, sin tocar el admin de Django.

### Fase 4 — Segmentación de destinatarios
- Carga por archivo (reusar mecanismo de `MailingJob`) + buscador interno (`search_bar.html` en `ajax_search_mode`).
- Lógica de aplicación "en caliente" sobre `RondaEncuesta` abierta (regla 12).
- **Salida**: alta/baja de destinatarios por ambos métodos, con impacto inmediato verificado en una ronda abierta de prueba.

### Fase 5 — Scheduler (apertura/cierre automático de rondas)
- Management command tipo `encuestas/management/commands/process_encuestas_rondas.py`, mismo patrón de loop que `process_mailing_jobs.py`/`process_ocr_jobs.py`.
- Nuevo servicio en `docker-compose.yml` (`encuestas_worker`, análogo a `ocr_worker`).
- Lógica: abre rondas según `intervalo_recurrencia_dias`, cierra rondas vencidas por `fecha_cierre_programada`.
- **Salida**: una encuesta recurrente de prueba abre y cierra rondas solo, sin intervención manual.

### Fase 6 — Middleware de bloqueo por encuesta obligatoria
- `encuestas/middleware.py` con `EncuestaObligatoriaMiddleware`, clon del patrón de `FirstLoginPasswordChangeMiddleware`/`ProfileConfirmationMiddleware`.
- Registrar en `MIDDLEWARE` (`config/settings.py`) después de `ProfileConfirmationMiddleware`.
- **Salida**: un usuario con ronda obligatoria pendiente queda bloqueado en cualquier vista del sistema salvo rutas exentas; test de middleware siguiendo el estilo de los tests ya existentes para los otros dos.

### Fase 7 — Modal y experiencia de respuesta
- Reusar `templates/components/modal.html` para el modal de encuesta pendiente.
- JS de mostrar/ocultar preguntas según condición de visibilidad.
- Vista `responder_ronda` (registra `RespuestaRonda`/`RespuestaPregunta`, respetando la regla de anonimato) + `snooze` (agenda `RecordatorioUsuario`).
- Mecanismo para exponer "próxima ronda pendiente" a `base.html` (ej. context processor liviano), dado que no existe hoy un middleware de "módulos visibles" del que colgarse.
- **Salida**: un usuario ve el modal al loguearse, puede responder o posponer (según corresponda), y la cola respeta el orden por vencimiento.

### Fase 8 — Resultados y exportación
- Dashboard con ApexCharts + tarjetas KPI (`.custom-card`) por pregunta, en vivo mientras la ronda está abierta.
- Exportación CSV vía `core/services/csv_export.py` y Excel vía patrón `openpyxl` (`VAT/services/nomina_export.py`), incluyendo metadatos de ronda/fecha/versión.
- **Salida**: quien tiene `ver_resultados` visualiza y exporta resultados de una ronda abierta y de rondas cerradas anteriores (comparación histórica).

### Fase 9 — Testing y cierre
- Cobertura de reglas críticas: anonimato + obligatoriedad (regla 1), bloqueo de edición con ronda abierta (regla 17), cola de pendientes (regla 12/criterio 12), aplicación en caliente de segmentación (regla 12).
- Revisar `docs/ia/TESTING.md` y `SECURITY_AI.md` antes de cerrar.
- Actualizar `AGENT_REPO_MAP.md` si la nueva app cambia hotspots de navegación relevantes (por `AGENTS.md`).
- Preparar PR desde `feature/modulo-encuestas` hacia `development`.

### Orden de dependencias entre fases
Fases 0→1→2 son estrictamente secuenciales (modelo antes que backend). Fases 3, 4 y 5 pueden avanzar en paralelo una vez cerrada la Fase 2 (UI, segmentación y scheduler no dependen entre sí). Fase 6 (middleware) y Fase 7 (modal) dependen de Fase 1 (modelos) y pueden avanzar en paralelo a las fases 3-5. Fase 8 (resultados) depende de que Fase 7 ya esté generando respuestas reales para tener datos de prueba. Fase 9 corre en paralelo a todas, sumando tests a medida que cada fase cierra.

---

Documento generado para servir de base al diseño técnico e implementación del módulo `encuestas`.
