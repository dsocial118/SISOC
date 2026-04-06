# VAT - fixture inicial de modalidades de cursado

Fecha: 2026-04-02

## Qué cambió

- Se agregó el fixture `VAT/fixtures/modalidad_cursada_inicial.json`.
- El fixture incorpora diez modalidades iniciales para el catálogo `ModalidadCursada`:
  - Educación Técnico Profesional
  - Educación Permanente de Jóvenes y Adultos
  - Educación Especial
  - No Corresponde
  - Educación de Formación Docente
  - Educación en Contextos de Privación de Libertad
  - Educación Rural
  - Educación Artística
  - Educación Común
  - Educación de Socio Humanística

## Motivo

- Facilitar la carga inicial del catálogo de modalidades de cursado en VAT con valores base acordados para el módulo.

## Validación prevista

- Validación sintáctica del JSON del fixture.
- Carga vía `load_fixtures` cuando se necesite poblar el entorno.