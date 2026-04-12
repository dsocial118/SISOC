# Buscador de cursos operativos VAT por texto

Fecha: 2026-04-11

## Qué se cambió

- Se agrega `GET /api/vat/cursos/buscar/?q=<texto>` en la API operativa de VAT.
- El endpoint busca por texto libre sobre nombre del curso, plan de estudio y título de referencia.
- La búsqueda se habilita a partir de 3 caracteres; si `q` falta o tiene menos de 3 letras devuelve `400`.
- La respuesta devuelve información enriquecida del curso, incluyendo:
  - centro con bloque anidado de provincia,
  - bloque `ciudad` dentro del centro con provincia, municipio, localidad y dirección,
  - modalidad y plan de estudio,
  - programa derivado,
  - parametrías de voucher,
  - comisiones asociadas con cupos, horarios, sesiones y ubicación.
- Se agrega el request correspondiente en la colección Postman `VAT - Planes Centros Cursos Comisiones`.

## Criterio funcional

- El buscador está pensado para clientes operativos que necesitan resolver cursos por texto sin hacer múltiples requests encadenadas.
- La búsqueda reutiliza el flujo operativo actual basado en `Curso` y `ComisionCurso`.
- El parámetro `q` es obligatorio y debe tener al menos 3 caracteres.

## Validación

- Se agregan tests automáticos para:
  - búsqueda exitosa con payload enriquecido,
  - rechazo cuando falta el parámetro `q`,
  - rechazo cuando el texto tiene menos de 3 caracteres.
