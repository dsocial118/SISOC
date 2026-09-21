# Centro de Infancia: nómina, asistencia y datos RENAPER

## Alcance

Este documento consolida los contratos actualmente implementados para la
asistencia sobre nómina y la precarga RENAPER en el alta de trabajadores de
Centro de Infancia (CDI). No reemplaza la guía de roles y pruebas funcionales
de SIMEPI/CDI.

## Asistencia sobre nómina

- La asistencia diaria usa `NominaCentroInfancia`, no `Trabajador`.
- Solo se muestran nóminas activas. Una nómina dada de baja se conserva para
  editar la asistencia de la fecha en que ya tiene un registro; una nómina
  pendiente no es elegible.
- Para cada fila, `presente=1` registra presencia, `presente=0` ausencia y la
  ausencia de marca elimina el registro de asistencia existente para esa fecha.
- La escritura valida las marcas recibidas, bloquea las nóminas y las
  asistencias involucradas, y se ejecuta en una única transacción.
- El calendario devuelve los días que tienen al menos una asistencia, sin
  distinguir presencia de ausencia ni exigir carga completa.
- La URL histórica de asistencia de trabajadores redirige a la asistencia de
  nómina, preservando los parámetros de consulta.

Las rutas de asistencia requieren `centrodeinfancia.change_centrodeinfancia`
y aplican el scope central del CDI. Ese scope delimita EGP por territorio,
referentes por `AccesoCDI` activo, trabajadores por `Trabajador.usuario` y los
roles nacionales por alcance nacional. El rol Auditoría no puede mutar CDI,
trabajadores, nóminas ni formularios.

## Integridad de la nómina vigente

Una persona puede tener, como máximo, una ficha de nómina **vigente** entre
todos los CDI. Para esta regla, vigente significa estado `Activo` o `Pendiente`.
Las fichas en `Baja` y las dadas de baja lógicamente no bloquean un alta ni una
derivación posterior.

- El alta, la reactivación por edición, el Django admin y la restauración desde
  la papelera aplican la misma regla y devuelven un mensaje neutro. No exponen
  el CDI en el que existe la ficha que provoca el conflicto.
- La derivación conserva el histórico: primero deja el origen en `Baja` y crea
  el destino en `Pendiente`, dentro de la misma transacción. También rechaza el
  flujo si la persona tiene una ficha vigente en un **tercer** CDI.
- Antes de persistir una operación que puede crear o reactivar vigencia, el
  servicio bloquea la fila de la persona y revalida bajo lock. Esto serializa
  intentos concurrentes desde CDI diferentes y evita que dos altas simultáneas
  dejen fichas vigentes.

La garantía es de aplicación sobre MySQL/InnoDB; no hay una constraint parcial
en base de datos porque MySQL no la implementa para este caso y los duplicados
históricos no se corrigen automáticamente. Antes de desplegar un cambio de
esta regla conviene revisar los duplicados vigentes existentes, ya que no se
modifican pero pueden bloquear derivaciones posteriores.

## Precarga y bloqueo RENAPER de trabajadores

- La búsqueda consulta RENAPER solo cuando no encuentra ciudadanos locales,
  el texto de búsqueda es numérico y tiene al menos siete dígitos.
- Los campos con valor provenientes de RENAPER se incluyen en un token firmado
  con el CDI y el usuario que inició el alta. El token vence a los 15 minutos.
- Al persistir, solo se aceptan valores que provengan de ese token. Se guardan
  los nombres de esos campos en `Trabajador.campos_verificados_renaper`.
- Esos campos se muestran deshabilitados tanto durante el alta como en la
  edición. Django conserva el valor inicial o de instancia, por lo que un POST
  no puede sobrescribirlo.
- No hay una excepción implementada para corregir un dato verificado por
  RENAPER; habilitarla requiere una decisión y una funcionalidad nueva.

## Rutas y permisos

| Flujo | Ruta | Permiso |
| --- | --- | --- |
| Asistencia de nómina | `/centrodeinfancia/<pk>/nomina/asistencia/` | `change_centrodeinfancia` |
| Calendario de asistencia | `/centrodeinfancia/<pk>/nomina/asistencia/calendario/` | `change_centrodeinfancia` |
| Edición de trabajador | `/centrodeinfancia/<pk>/trabajadores/<trabajador_id>/editar/` | `change_trabajador` |

## Referencias de implementación y validación

- `centrodeinfancia/services.py`: `AsistenciaNominaCentroInfanciaService`.
- `centrodeinfancia/services.py`: validación y serialización de nómina vigente
  por persona (`tiene_nomina_cdi_vigente_en_otro_centro`).
- `centrodeinfancia/views.py`: `AsistenciaNominaCentroView`, calendario y
  `TrabajadorCentroInfanciaCreateView`.
- `centrodeinfancia/urls.py`: protección de rutas y redirección histórica.
- `centrodeinfancia/tests/test_asistencia_nomina.py` y
  `centrodeinfancia/tests/test_trabajadores_views.py`: regresión de asistencia
  y flujo de trabajador.
- `docs/registro/cambios/2026-07-16-cdi-validaciones-trabajador.md`:
  validaciones, migraciones y contrato RENAPER.
- `docs/registro/cambios/2026-07-17-cdi-asistencia-nomina.md`: reglas de
  negocio y compatibilidad de asistencia.
- `docs/registro/cambios/2026-07-15-cdi-enforcement-alcances.md`: alcance por
  rol y restricción de Auditoría.
- `docs/registro/cambios/2026-08-07-cdi-nomina-vigente-en-un-solo-centro.md`:
  alcance, concurrencia, límites y rollback de la exclusividad de vigencia.
- `docs/qa/2038-roles-simepi-cdi-guia-testeo.md`: guía funcional de roles.

## Validación de identidad en el alta de nómina (issue #2508, Fase 1)

La precarga del niño/a firma DNI, apellido, nombre, fecha y datos RENAPER con
un salt propio de nómina, CDI, usuario y vencimiento de 15 minutos. Un ciudadano
nuevo queda VALIDADO solo si la firma es válida y esos cuatro datos coinciden
con el formulario validado. La comparación tolera mayúsculas y espacios, pero
no elimina tildes ni cambia letras; la fecha se compara como fecha de calendario.
Si se modifica la identidad o el token falta, vence o pertenece a otro usuario
/CDI, el alta sigue como manual y NO_CONSULTADO. El POST de origen_dato no decide
el origen ni la validación. Si hay errores de formulario, se conserva el token
sin renovar su vigencia ni consultar nuevamente RENAPER.

Los ciudadanos locales se reutilizan sin alterar su validación. El helper
ciudadanos/services_renaper_validacion.py conserva el payload de la importación
masiva: estado, fecha actual, datos_api (o data como fallback) y origen renaper.
No se crean ciudadanos para los responsables legales.

### Indicador compartido

centrodeinfancia/services_renaper_estado.py expone estado_renaper_nomina y
build_adult_validation_map. El primer servicio devuelve renaper_nino,
renaper_responsable_1 y renaper_responsable_2, con etiquetas Sí/No. El segundo
permite preparar los DNI por lote para evitar consultas por fila.

El PDF provincial consume este cálculo con su mismo contrato: niño validado
según Ciudadano y adulto 1 únicamente cuando existe una coincidencia por
Documento y está validada. Múltiples ciudadanos para un DNI dan No aunque todos
estén validados. Se conserva el manager que excluye borrados lógicos.

### Revalidación operativa

El comando validar_renaper_nominas_cdi selecciona ciudadanos no eliminados, con
documento, NO_CONSULTADO y al menos una nómina CDI no eliminada. Incluye fichas
activas, pendientes y bajas; cada ciudadano se consulta una sola vez por corrida.

- --batch-size (500 por defecto) controla la lectura del queryset.
- --limit limita ciudadanos consultados; ambos valores deben ser positivos.
- --dry-run consulta RENAPER real pero **no escribe**. Requiere la misma ventana
  operativa acordada que una corrida efectiva.
- Si el sexo local corresponde a M/F/X, se consulta ese sexo; si no, se intenta
  M, F y X hasta encontrar coincidencia, como la importación masiva sin sexo.
- Coincidencia de apellido, nombre y fecha completos: VALIDADO, fecha, datos y
  origen renaper. Discrepancia o no_match: NO_VALIDADO, motivo OTRO y descripción
  del resultado, sin atribuir una causa no demostrada ni reemplazar la identidad.
- Error sistémico, respuesta inválida, error desconocido o fallecido interrumpen
  la corrida sin convertir el problema en una no validación.

Los resultados se reúnen en memoria antes de escribir. Un error incluso en el
último lote deja **toda la corrida sin marcas**. La escritura se hace en una
transacción posterior a las consultas externas; bloquea cada ciudadano en orden
de PK y sus vínculos CDI, verifica que siga pendiente y compara su identidad con
la leída antes de consultar. Los cambios concurrentes se omiten y quedan para
una nueva ejecución. Una falla de escritura revierte toda la transacción.

Contadores: consultados (ciudadanos, no llamadas por sexo), validados y
no_validados (resultados propuestos), omitidos (cambios concurrentes), escritos
(confirmados) y errores. Un dry-run o una corrida abortada siempre informa cero
escritos. Los contadores y errores no incluyen documentos ni respuestas externas.

No se agregó migración ni se cambió tipo_registro_identidad. Se usa update de
campos de validación, como el backfill existente, porque Ciudadano.save normaliza
identidad y borra los motivos para registros ESTANDAR. **Limitación previa:** un
guardado posterior por otro circuito puede borrar esos motivos; este cambio no
modifica esa normalización. El indicador usa el estado, que ese guardado conserva.

### Riesgos y reversibilidad

La memoria requerida depende del universo consultado y del tamaño de los datos
RENAPER. --limit acota memoria, duración y llamadas; --batch-size no crea commits
parciales. Los locks de escritura deben verificarse en MySQL; los tests de cambios
simulados no demuestran la exclusión entre conexiones reales.

Revertir el código no revierte las marcas de una corrida ya confirmada. Antes de
una operación real se necesita un respaldo autorizado de los campos afectados
para una eventual restauración selectiva. No se debe borrar masivamente estados
ni reabrir validaciones de otros circuitos.
