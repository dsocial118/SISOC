## 2026-03-29 - Información Institucional mobile

### Contexto

Se alineó el módulo de Información Institucional de SISOC Mobile con el alcance funcional definido para espacio, organización, referente, convenio y relevamiento.

### Cambios

- Se amplió `GET /api/comedores/{id}/` para incluir `relevamiento_actual_mobile`, un resumen legible del último relevamiento del espacio con preguntas y respuestas preparadas para mobile.
- Se optimizó el `prefetch` del detalle de comedor para evitar consultas adicionales al serializar el relevamiento actual.
- Se reordenó la pantalla mobile de Información Institucional para mostrar:
  - contexto del espacio: comedor, organización y programa
  - datos de organización
  - datos del espacio
  - datos del referente
  - colaboradores
  - datos de convenio
  - datos de relevamiento
- Se incorporó cobertura de API para validar que el detalle del comedor entregue el resumen de relevamiento esperado para mobile.

### Supuestos

- `Prestaciones GESCOM` se resuelve provisoriamente con `codigo_de_proyecto` hasta definir un campo backend específico para convenio en mobile.
- `Fecha de inicio de convenio`, `monto total del convenio` y `domicilio electrónico del comedor` permanecen como `Sin dato` cuando no existe un campo confiable en el modelo actual.
