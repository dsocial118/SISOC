# Dominio

## 1) Glosario
- Comedor: establecimiento (comedor/merendero) con ubicación, estado, programa y referente. Evidencia: comedores/models.py:203-405.
- Relevamiento: visita/encuesta a un comedor con datos operativos y estado. Evidencia: relevamientos/models.py:986-1084.
- Referente: persona de contacto del comedor. Evidencia: comedores/models.py:30-92.
- Dupla: equipo técnico asignado a comedores (relación en Comedor.dupla). Evidencia: comedores/models.py:257-262.
- Estado (actividad/proceso/detalle): estructura jerárquica para estados de comedores e historial. Evidencia: comedores/models.py:106-200.
- Observación: nota asociada a un comedor con fecha de visita. Evidencia: comedores/models.py:500-518.
- Nómina: asociación comedor↔ciudadano con estado (pendiente/activo/baja). Evidencia: comedores/models.py:451-488.
- Territorial/GESTIONAR: sistema externo con el que se sincronizan comedores/relevamientos. Evidencia: comedores/tasks.py:1-249; relevamientos/tasks.py:1-144.

## 2) Entidades core
| Modelo | Significado | Campos clave | Invariantes |
| --- | --- | --- | --- |
| Comedor | Establecimiento gestionado (comedor/merendero). | `nombre`, `programa`, `tipocomedor`, `provincia/municipio/localidad`, `dupla`, `referente`, `estado`, `estado_validacion`, `ultimo_estado`. Evidencia: comedores/models.py:203-405. | `estado` choices (“Sin Ingreso”, “Asignado…”); `estado_validacion` choices (Pendiente/Validado/No Validado); `latitud/longitud` con rangos; validación de direcciones via regex; `delete` limpia historial antes de borrar. Evidencia: comedores/models.py:264-396. |
| EstadoActividad/Proceso/Detalle + EstadoGeneral/Historial | Taxonomía y tracking de estados de comedores. | FK encadenados (actividad→proceso→detalle), `EstadoHistorial.comedor`, `estado_general`, `fecha_cambio`. Evidencia: comedores/models.py:106-200. | Historial ordenado desc; `ultimo_estado` en Comedor apunta a último registro. Evidencia: comedores/models.py:176-200,278-285. |
| Referente | Contacto del comedor. | `nombre`, `apellido`, `mail`, `celular`, `documento`, `funcion`. Evidencia: comedores/models.py:30-92. | `clean` valida celular (≤15 dígitos) y documento (7 u 8 dígitos); `save` ejecuta `full_clean`. Evidencia: comedores/models.py:60-84. |
| Relevamiento | Registro de visita/encuesta al comedor. | `comedor`, `estado`, `fecha_visita`, `territorial_uid/nombre`, varias OneToOne a componentes (espacio, recursos, etc.), `responsable_relevamiento`, `docPDF`. Evidencia: relevamientos/models.py:986-1040,1018-1034. | Único por `comedor` + `fecha_visita`; validación evita más de un relevamiento activo (“Pendiente”/“Visita pendiente”); puede asignar responsable al referente del comedor. Evidencia: relevamientos/models.py:1050-1071. |
| Observacion | Nota con fecha sobre un comedor. | `comedor`, `observador`, `fecha_visita`, `observacion`. Evidencia: comedores/models.py:500-518. | Índice por comedor; sincroniza con GESTIONAR en post_save. Evidencia: comedores/signals.py:70-75. |
| Nomina | Relación comedor↔ciudadano con estado. | `comedor`, `ciudadano`, `estado` (pendiente/activo/baja), `fecha`. Evidencia: comedores/models.py:451-488. | Estado con choices; index por comedor. Evidencia: comedores/models.py:451-488. |
| MontoPrestacionPrograma | Valores monetarios de cada tipo de prestación alimentaria por programa. Permite configurar via ABM el precio de desayuno, almuerzo, merienda y cena para cada programa (ej. PNUD Secos, PAC). Los cálculos de monto mensual en el detalle del comedor usan estos valores; si no existe registro para el programa del comedor se aplican valores por defecto. | `programa` (nombre del programa), `desayuno_valor`, `almuerzo_valor`, `merienda_valor`, `cena_valor`, `usuario_creador`. Evidencia: core/models.py:9-55; core/views.py; core/urls.py. | Todos los valores son opcionales (blank/null); el cálculo hace fallback a valores fijos si no hay registro para el programa. Evidencia: comedores/services/comedor_service.py. |

## 3) Relaciones importantes
- Comedor tiene FK a Programa, TipoDeComedor, Provincia/Municipio/Localidad, Dupla, Referente, Organizacion; historial de estados (`EstadoHistorial`) y observaciones/nóminas. Evidencia: comedores/models.py:225-405,176-200,500-518,451-488.
- Relevamiento FK a Comedor; OneToOne a subcomponentes (FuncionamientoPrestacion, Espacio, Colaboradores, FuenteRecursos, FuenteCompras, Prestacion, Anexo, Excepcion, PuntoEntregas). Evidencia: relevamientos/models.py:986-1034.
- Referente puede ligarse a múltiples comedores y relevamientos (responsable). Evidencia: comedores/models.py:341-343; relevamientos/models.py:1018-1024.
- EstadoGeneral agrupa estado_actividad/proceso/detalle; EstadoHistorial vincula Comedor ↔ EstadoGeneral (timeline). Evidencia: comedores/models.py:152-200.

## 4) Estados y transiciones
- Comedor.estado: choices “Sin Ingreso”, “Asignado a Dupla Técnica” (filtro operativo). Evidencia: comedores/models.py:264-276.
- Comedor.estado_validacion: choices Pendiente/Validado/No Validado; `fecha_validado` opcional. Evidencia: comedores/models.py:347-365.
- Estados jerárquicos manejados vía EstadoHistorial + `ultimo_estado`; no se declaran máquinas de estado explícitas. Evidencia: comedores/models.py:278-285,176-200.
- Relevamiento.estado: libre (CharField) pero validación restringe duplicados cuando estado ∈ {“Pendiente”, “Visita pendiente”}. Evidencia: relevamientos/models.py:988-1064.
- Nomina.estado: choices pendiente/activo/baja. Evidencia: comedores/models.py:451-476.

## 5) Reglas de negocio no obvias
- No puede haber más de un relevamiento activo (Pendiente/Visita pendiente) por comedor; `save` valida y bloquea. Evidencia: relevamientos/models.py:1050-1064.
- Cambios de programa del comedor se auditan en `AuditComedorPrograma` al cambiar FK programa. Evidencia: comedores/signals.py:31-52; comedores/models.py:407-449.
- Al crear/actualizar Comedor/Referente/Observacion se dispara sincronización a GESTIONAR (asincrónica). Evidencia: comedores/signals.py:24-82.
- Al eliminar Comedor se limpia `ultimo_estado` y su historial en transacción. Evidencia: comedores/models.py:382-396.
- Relevamiento puede forzar responsable al referente del comedor cuando `responsable_es_referente=True`. Evidencia: relevamientos/models.py:1042-1049.

## 6) Eventos colaterales (signals, tasks, side effects)
- post_save Comedor → `AsyncSendComedorToGestionar`; pre_save Comedor → audit de cambio de programa y sync; pre_delete Comedor → `AsyncRemoveComedorToGestionar`. Evidencia: comedores/signals.py:24-68.
- post_save Observacion/Referente → sync con GESTIONAR. Evidencia: comedores/signals.py:70-82.
- post_save Relevamiento → clasifica comedor (ClasificacionComedorService). Evidencia: comedores/signals.py:91-93.
- Tasks usan hilos y llamadas HTTP a GESTIONAR; relevamientos/comedores exportan payloads y actualizan docPDF/estado externo. Evidencia: comedores/tasks.py:1-249; relevamientos/tasks.py:1-144.

## 7) Permisos a nivel dominio
- Roles/grupos creados por comando incluyen “Comedores Listar/Crear/Ver/Editar/Eliminar”, “Comedores Relevamiento Ver/Crear/Detalle/Editar”, “Comedores Observaciones …”, “Comedores Nomina …”, roles técnicos, legales, contables y dashboards. Evidencia: users/management/commands/create_groups.py:1-61.
- Acceso API/Views protegido por auth Django y `IsAuthenticated` por defecto en DRF. Evidencia: config/settings.py:130-135,195-203.
- No se documentan restricciones adicionales por objeto (permisos granulares no visibles en modelos). Evidencia: DESCONOCIDO.

## Notas de negocio (provistas)
- Objeto principal: Comedor y sus modelos relacionados.
- Flujos críticos: sincronización con GESTIONAR, mantenimiento de información real en comedores y relevamientos, filtrado avanzado de listas.
- Datos sensibles: indicado como “no hay datos sensibles”; no se evidencian reglas de masking en código.

## TODOs
- Documentar reglas de permisos a nivel objeto/filtrado avanzado si existen en vistas/serializers (no evidente en modelos). Evidencia: DESCONOCIDO.
