# Reparación de mojibake en datos y exportaciones

Fecha: 2026-09-01

## Problema confirmado

La nómina provincial de niños genera un PDF Unicode válido, pero algunos
apellidos y nombres llegan al generador con mojibake, por ejemplo secuencias
como `Ã…`, `Â…` o `â…`. Los títulos estáticos y otros textos Unicode del mismo
PDF se renderizan correctamente.

La inspección read-only de producción confirmó:

- cliente, conexión, servidor y base MySQL usan `utf8mb4`;
- las columnas `apellido` y `nombre` de `Ciudadano` y
  `NominaCentroInfancia` usan `utf8mb4/utf8mb4_0900_ai_ci`;
- existen 198.688 ciudadanos candidatos a mojibake sobre 3.102.880;
- existen 26 fichas CDI candidatas, 21 activas y visibles en el PDF;
- las 26 fichas CDI afectadas también tienen afectado su `Ciudadano`;
- 171.119 candidatos declaran origen RENAPER y 198.677 fueron creados en 2026.

Por lo tanto, BOM, ReportLab y la configuración vigente de MySQL quedan
descartados como causa del caso reportado. El problema está en texto que fue
decodificado incorrectamente antes de persistirse.

## Decisión

La corrección será conservadora y en capas:

1. Decodificar respuestas JSON de RENAPER desde sus bytes como UTF-8 estricto,
   sin confiar en un `charset` HTTP incorrecto.
2. Normalizar en el límite RENAPER únicamente secuencias de mojibake que puedan
   reconstruirse como bytes UTF-8 válidos.
3. Reutilizar la misma normalización en la nómina PDF como defensa temporal
   para datos históricos todavía no reparados.
4. Proveer un comando de administración con `dry-run` por defecto para auditar
   y reparar por lotes `apellido` y `nombre` en `Ciudadano` y
   `NominaCentroInfancia`.
5. No elegir una tabla como fuente funcional de otra ni reemplazar nombres por
   semejanza. Sólo se cambia una secuencia cuando su inversión de bytes es
   exacta y determinística.

## Algoritmo de reparación

El texto se recorre buscando caracteres que representan el primer byte de una
secuencia UTF-8 interpretada como Windows-1252 o Latin-1. La longitud esperada
se obtiene del byte inicial; los caracteres siguientes deben reconstruir bytes
de continuación válidos y el conjunto debe decodificar estrictamente como
UTF-8.

La reparación se repite un máximo acotado de veces para cubrir datos
doblemente recodificados. Texto correcto, secuencias incompletas y casos
ambiguos permanecen sin cambios. La operación es idempotente.

La conversión de una cadena completa queda descartada: producción contiene
campos que mezclan caracteres correctos y rotos, y una recodificación global
dañaría los primeros.

## Comando operativo

El comando:

- no escribe salvo que se indique explícitamente `--apply`;
- informa sólo conteos por modelo/campo, sin nombres, documentos ni muestras;
- procesa con `iterator` y actualizaciones por lotes;
- modifica únicamente valores donde el reparador produjo un cambio válido;
- puede limitarse por modelo, campo y tamaño de lote;
- es reejecutable sin volver a modificar valores ya reparados.

La ejecución productiva queda fuera del PR. Antes de autorizarla se requiere:

1. ejecutar el `dry-run` sobre la versión desplegada;
2. obtener backup consistente de las tablas afectadas;
3. registrar conteos esperados y duración;
4. aprobar una ventana operativa;
5. ejecutar por lotes y repetir el `dry-run`, que debe devolver cero cambios.

## Validación

- Pruebas unitarias del reparador con tildes, eñe, mayúsculas, comillas,
  contenido mixto, doble recodificación, entradas correctas e incompletas.
- Pruebas de la integración RENAPER con JSON UTF-8 y cabecera HTTP incorrecta.
- Regresión del PDF con snapshot y ciudadano históricamente afectados.
- Pruebas del comando en `dry-run`, `--apply`, lotes e idempotencia.
- Ejecución focalizada mediante el entorno Docker-first del repositorio.

## Alternativas descartadas

- Añadir BOM al PDF: no aplica a ese formato y no cambia datos ya corruptos.
- Reparar sólo al exportar: oculta la corrupción y deja otros consumidores
  expuestos.
- Ejecutar un `UPDATE ... CONVERT(...)` sobre columnas completas: producción
  contiene textos mixtos y la conversión no es segura.
- Copiar siempre desde `Ciudadano` hacia la ficha CDI: cambia el contrato
  funcional del snapshot y no resuelve los ciudadanos ya afectados.
