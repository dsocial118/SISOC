# PAS: Formación sin integración externa

Fecha de revisión: 2026-08-31

## Decisión

La pantalla de Formación PAS queda visible como interfaz pendiente, sin consultar
VAT ni otro dominio. Hasta contar con una definición funcional y un contrato
público estable, los servicios devuelven una colección vacía y puntaje neutro.

## Motivo

No existe una definición confirmada que permita equiparar inscripciones, estados
o puntajes de VAT con la condicionalidad FCH de PAS. Consumir sus modelos de forma
directa acoplaría ambos dominios y convertiría supuestos en reglas de negocio.

## Consecuencias

- PAS no importa modelos, servicios ni tablas de VAT.
- La navegación y la selección del titular funcionan aunque la fuente esté pendiente.
- Una integración futura deberá entrar por una fachada pública y acompañarse de
  reglas funcionales, permisos y pruebas específicas.
