# Reparación de mojibake capitalizado con minúsculas

Fecha: 2026-09-01

## Problema confirmado

Después de aplicar la reparación de mojibake capitalizado del PR #2421, el
PDF provincial CDI de Buenos Aires conserva nombres como
`Benjam\u00e3\u00adN`, `Nicol\u00e3\u00a1S` e `Isa\u00e3\u00adAs`.
Ciudadano y el snapshot de Nómina CDI contienen los mismos valores.

Los pares siguen siendo reversibles: `\u00e3\u00ad` representa `í`,
`\u00e3\u00a1` representa `á` y `\u00e3\u00b3` representa `ó`. La reparación
anterior sólo aceptaba pares que reconstruían una letra mayúscula. Estos casos
reconstruyen una letra minúscula y conservan una mayúscula artificial después
del límite de palabra creado por `str.title()`.

El PDF también expone `ÁNabelle`. Ese valor proviene de una secuencia estándar
ya reparada a `Á`, pero mantiene la segunda mayúscula artificial del mismo
flujo histórico. Su forma reversible es `Ánabelle`.

## Alcance aprobado

- Extender el servicio común de reparación con condiciones estrictas para las
  dos variantes confirmadas.
- Normalizar sólo el token afectado, no el nombre o apellido completo.
- Reutilizar el comando existente sobre Ciudadano y Nómina CDI y la defensa
  de salida del PDF.
- Mantener dry-run por defecto y `--apply` como única escritura.
- No inferir tildes ausentes ni corregir grafías sin evidencia reversible.
- No cambiar modelos, migraciones, dependencias ni semántica RENAPER.

## Algoritmo

### Par que reconstruye una minúscula

Se acepta `ã` seguido por un carácter que reconstruye un byte de continuación
UTF-8 sólo cuando:

1. `C3 <continuación>` decodifica estrictamente a una letra minúscula;
2. después del par existe una letra mayúscula, evidencia del falso límite
   creado por `str.title()`.

Se reemplaza el par y se reaplica `title()` únicamente al token que lo
contiene. Así `Isa\u00e3\u00adAs` queda `Isaías`.

### Mayúscula acentuada con segundo inicio artificial

Se normaliza un token que comienza con una letra latina acentuada mayúscula,
seguida por otra mayúscula y luego por una minúscula. La condición excluye
palabras completamente en mayúsculas y texto ya correctamente capitalizado.
Así `ÁNabelle` queda `Ánabelle`.

Los nombres correctos con `ã`, como `João` y `São Tomé`, no cumplen el patrón
de byte de continuación y permanecen sin cambios.

## Seams de prueba aprobados

1. `repair_utf8_mojibake`: casos productivos `Isaías`, `Simón`, `Tomás`,
   `Benjamín`, `Nicolás`, `Valentín`, `Agustín`, `Jazmín`, `Lía`, `León` y
   `Ánabelle`; preservación e idempotencia de Unicode correcto.
2. `repair_utf8_mojibake`: comando Django en dry-run, `--apply` e
   idempotencia sobre Ciudadano y Nómina CDI.
3. `build_export_data`: el snapshot CDI continúa siendo la fuente y entrega
   los nombres reparados al PDF.

## Operación productiva

El despliegue no escribe datos. Después del deploy se repite el flujo
controlado: dry-run, revisión agregada, backup consistente, ventana y
autorización, `--apply`, segundo dry-run en cero y smoke autenticado del PDF.

## Alternativas descartadas

- Lista cerrada de registros: no cubre otros datos con el mismo patrón.
- Corrección exclusiva del PDF: conserva la corrupción en las fuentes.
- Aplicar `title()` a todo el campo: puede alterar capitalización legítima no
  relacionada con la secuencia reparada.
