# Buscador de cursos operativos VAT por texto

Fecha: 2026-04-11

## Qué se cambió

- Se agrega `GET /api/vat/cursos/buscar/?q=<texto>` en la API operativa de VAT.
- El endpoint busca por texto libre sobre nombre del curso, plan de estudio y título de referencia.
- Sin `q` devuelve la primera carga paginada del listado operativo de cursos.
- La búsqueda por texto se habilita a partir de 3 caracteres; si `q` se envía con menos de 3 letras devuelve `400`.
- Tanto la primera carga como la búsqueda devuelven solo cursos activos que tengan al menos una comisión activa.
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
- El parámetro `q` es opcional para permitir primera carga y limpieza del campo de búsqueda.
- Cuando `q` se envía con contenido, debe tener al menos 3 caracteres.
- El resultado queda restringido a opciones vigentes de inscripción: curso activo y al menos una comisión activa.

## Validación

- Se agregan tests automáticos para:
  - búsqueda exitosa con payload enriquecido,
  - listado paginado cuando falta el parámetro `q`,
  - listado paginado cuando `q` queda vacío,
  - rechazo cuando el texto tiene menos de 3 caracteres.
