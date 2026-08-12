# Bounded context Comedores Core

## Decisión

Comedores Core se mantiene como un bounded context lógico dentro del monolito.
No se crea una app nueva, se mueven modelos ni se cambian migraciones. Su
membresía inicial es `comedores`, `admisiones`, `relevamientos`,
`organizaciones`, `duplas`, `expedientespagos`, `rendicioncuentasfinal`,
`rendicioncuentasmensual`, `intervenciones` y `acompanamientos`.

`pwa` e `importarexpediente` son adaptadores del contexto: conservan tablas y
flujos propios, pero sus referencias y operaciones comparten consistencia con
Comedores Core. No se los trata como verticales extraíbles en este corte.

Dashboard es un consumidor externo. Obtiene métricas mediante `comedores.api`
y `relevamientos.api`; los dominios dueños registran sus observers, por lo que
Dashboard no importa modelos ni señales del cluster.

Los receivers de Admisiones, Intervenciones, Relevamientos, Comedores y
Organizaciones viven en sus dominios dueños y usan `audittrail.api` para
delegar la persistencia del evento. Audittrail sólo conserva metadatos y el
contrato público; no importa los modelos del contexto.

La FK histórica `centrodefamilia.Centro.organizacion_asociada` hacia
`Organizacion` se conserva como excepción de esquema: cambiarla exige una
migración de datos y revisar la semántica de borrado en un corte dedicado. El
contrato de imports permite únicamente ese borde declarado; todo otro consumo
externo debe pasar por una API pública.

## Evidencia y consecuencias

- Comedor tiene relaciones con Organización, Dúpla, Admisión y Nómina;
  Relevamientos, Expedientes y Rendiciones referencian Comedor.
- La importación de expedientes usa transacciones y bloqueos que actualizan
  expediente y estado del comedor como una sola operación.
- PWA persiste referencias a Comedor y Nómina, y ejecuta reglas de nómina,
  asistencia y convenios.

Los ciclos entre miembros se aceptan temporalmente. Los consumidores externos
deben usar una fachada por capacidad, con IDs y proyecciones estables, nunca
modelos o QuerySets.
