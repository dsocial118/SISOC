# Boundaries públicos de Fase 3

## Decisión

Los dominios `dispositivos`, `VAT`, `ver_para_ser_libre`, `centrodefamilia` y
`centrodeinfancia` permanecen dentro del monolito modular. No se crean
deployables, APIs HTTP internas ni migraciones de datos.

- Dispositivos y VAT no tenían consumidores Python de negocio: sus internals
  quedan prohibidos para los demás dominios. La ruta de preview de VAT se
  compone desde `VAT.global_urls`, no desde una view interna.
- Ver para Ser Libre es independiente de Comedores: no hay FKs ni transacciones
  compartidas. Su resolución de ciudadanos usa `ciudadanos.api` y la fachada
  RENAPER compartida.
- Dashboard consume el agregado `centrodefamilia.api.obtener_metricas_dashboard`
  en vez de consultar modelos CDF.
- Centro de Infancia conserva sus registros e invariantes. Intervenciones es el
  dueño del catálogo que CDI consume mediante `intervenciones.api`; las FKs de
  catálogo existentes no cambian de ownership.
- Los receivers de auditoría de CDI viven en el dominio y utilizan
  `audittrail.api`, de modo que Audittrail ya no importa modelos CDI.

## Protección

`.importlinter` prohíbe imports externos a los internals de los cinco dominios,
impide que VPSL vuelva a depender de Comedores y fuerza a CDI a consumir el
catálogo público de Intervenciones.

## Consecuencias

Los contratos son Python internos al monolito. El adaptador de formularios de
CDI conserva querysets de catálogo para mantener el contrato de los campos
Django; no constituye una API de transporte ni un límite de extracción. La
extracción futura sigue requiriendo evaluación separada de ownership de datos,
consistencia transaccional y operación.
