# Reparación de mojibake capitalizado

Fecha: 2026-09-01

## Problema confirmado

La primera reparación productiva de mojibake dejó en cero los cambios
reversibles según el algoritmo original, pero el PDF CDI todavía mostró datos
históricos con una variante distinta. El valor persistido contiene una
secuencia como `Lu\u00e3\u0081N`.

La causa es una transformación en dos pasos:

1. texto UTF-8 en mayúsculas fue interpretado como Latin-1/Windows-1252;
2. el flujo histórico aplicó `str.title()` sobre el mojibake.

Por ejemplo, `LUÁN` pasó primero a `LUÃ\x81N` y luego a
`Lu\u00e3\u0081N`. La capitalización convirtió `Ã` en `ã` y creó un nuevo
límite de palabra delante de la última letra. El reparador original no puede
invertir esa forma porque `ã` representa normalmente el byte `E3`, no el byte
`C3` del mojibake previo.

## Alcance aprobado

- Reparar la variante capitalizada en el servicio común de encoding.
- Reutilizar el resultado en el comando existente y en el PDF CDI.
- Mantener el dry-run como modo por defecto y `--apply` como única escritura.
- No modificar la columna ni la semántica de validación RENAPER.
- No agregar migraciones, dependencias, rutas ni cambios de modelo.

## Algoritmo

Antes de las pasadas existentes se busca un patrón acotado:

- carácter `ã`;
- seguido por un carácter que reconstruye un byte de continuación UTF-8;
- el par `C3 <continuación>` debe decodificar estrictamente;
- el resultado debe ser una letra Unicode mayúscula.

Sólo si se cumple todo se reemplaza el par. Como el patrón demuestra que el
texto ya había pasado por `str.title()`, se reaplica `title()` al valor reparado
para eliminar el falso límite de palabra. Así `Lu\u00e3\u0081N` se convierte
en `Luán`.

La restricción a una letra mayúscula evita tratar como corrupción una `ã`
legítima de nombres portugueses. Los casos ambiguos continúan sin cambios.

## Seams de prueba aprobados

1. `repair_utf8_mojibake`: reproduce el valor productivo escapado y preserva
   texto correcto, incluido `João` y `Donatto Simón`.
2. `repair_utf8_mojibake`: comando Django en dry-run, `--apply` e idempotencia
   sobre Ciudadano y Nómina CDI.
3. `build_export_data`: el PDF recibe `Luán` sin cambiar la fuente funcional
   del snapshot.

## Operación productiva

El PR no escribe datos. Después del despliegue se requiere:

1. dry-run sobre Ciudadano y Nómina CDI;
2. guardar conteos y duración;
3. backup consistente y recuperable de ambas tablas;
4. ventana y autorización operativa;
5. ejecución con `--apply`;
6. segundo dry-run con cero cambios reversibles;
7. smoke autenticado del PDF CDI.

Los conteos del nuevo dry-run no deben compararse como equivalentes con el
primer saneamiento: este cambio incorpora una clase que antes no era detectable.

## Alternativas descartadas

- Corregir sólo el PDF: ocultaría datos corruptos a otros consumidores.
- Actualizar únicamente el caso reportado: dejaría otros valores del mismo
  patrón sin tratamiento.
- Aplicar `title()` a todo texto: alteraría valores correctos sin evidencia de
  mojibake capitalizado.
