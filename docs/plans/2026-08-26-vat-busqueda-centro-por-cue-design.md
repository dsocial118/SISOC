# Búsqueda integral de Centros VAT por CUE

Fecha: 2026-08-26

## Objetivo

Permitir que una integración o una persona consulte un Centro VAT mediante su
CUE sin introducir una ruta nueva: `GET /api/vat/centros/?cue=<CUE>`.

## Contrato aprobado

- Conserva la paginación actual de `/api/vat/centros/` (`count`, `next`,
  `previous`, `results`).
- Sin `cue`, mantiene el serializer y comportamiento previos.
- Con `cue`, normaliza un valor numérico de hasta nueve dígitos completando
  ceros a la izquierda y realiza coincidencia exacta.
- Busca el CUE en `InstitucionIdentificadorHist` tanto vigente como histórico,
  y también en `Centro.codigo` como compatibilidad para datos legacy.
- Devuelve cada Centro coincidente con una ficha institucional/formativa
  ampliada. Si existiera un dato anómalo que relacione un CUE con más de un
  Centro, la semántica de listado devuelve todos los resultados.

## Información incluida

- Identidad, ubicación, contacto institucional y responsable del Centro.
- CUE consultado, CUE actual, identificadores vigentes/históricos y origen de
  la coincidencia.
- Sedes, anexos, dependencias y puntos de atención.
- Cursos, planes, títulos, modalidades, parametrías de voucher institucionales
  y sus comisiones, horarios y sesiones.
- Oferta institucional legacy y sus comisiones, horarios y sesiones.

## Privacidad y autorización

El endpoint conserva `HasAPIKey`. No expone alumnos, ciudadanos, inscripciones,
evaluaciones, resultados, vouchers individuales, usuarios internos ni el
documento de los contactos institucionales.

## Errores y compatibilidad

- `400` para `cue` vacío, no numérico o de más de nueve dígitos.
- `200` con `count: 0` cuando no hay coincidencias.
- `401` cuando falta la API key o es inválida.
- No se cambian modelos, migraciones, permisos ni los recursos CRUD existentes.

## Validación prevista

- CUE vigente e histórico, incluido normalizado sin ceros iniciales.
- Sin coincidencias, valor inválido y ausencia de API key.
- Paginación habitual y presencia de las relaciones institucionales/formativas.
- Ausencia del documento de contacto y de recursos personales.
