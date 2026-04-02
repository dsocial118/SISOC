# 2026-04-01 - Modelo funcional de vouchers para VAT

## Estado

- propuesta

## Contexto

En VAT ya existe una base funcional para vouchers, ofertas institucionales e
inscripciones, pero el comportamiento esperado no quedó documentado de forma
integral.

Esto generó ambiguedades en varios puntos:

- qué representa la parametría de voucher,
- cómo se asigna un voucher a una carrera o a un curso,
- cuándo se consume el crédito,
- qué reglas deben cumplirse antes de permitir una inscripción,
- cómo deben convivir carrera y curso con una lógica homogénea,
- y cómo distinguir errores de configuración del producto frente a errores del
  ciudadano.

Además, el análisis del código actual mostró brechas entre la lógica esperada y
la implementación real, sobre todo en consumo, selección de vouchers válidos y
alineación entre web y API.

## Objetivo

Definir un modelo funcional único para vouchers en VAT que sirva como referencia
para:

- diseño funcional,
- implementación en backend,
- validaciones de formularios y API,
- documentación operativa,
- y revisión de bugs/regresiones.

## Decisión

Se adopta el siguiente modelo funcional para vouchers en VAT.

### 1. Entidades funcionales

#### 1.1 Parametría de voucher

La parametría define el tipo de voucher.

Responsabilidades funcionales:

- identificar el programa al que pertenece,
- definir el tipo de beneficio,
- establecer si aplica a carrera, curso o ambos,
- almacenar estado y metadata general,
- servir como criterio de elegibilidad para productos formativos.

La parametría responde a la pregunta:

- "qué clase de voucher existe y para qué sirve"

#### 1.2 Voucher del ciudadano

El voucher es la instancia concreta asignada a un ciudadano.

Responsabilidades funcionales:

- vincular ciudadano + parametría,
- almacenar créditos disponibles,
- registrar fecha de asignación y vencimiento,
- definir estado operativo,
- permitir auditoría del ciclo de vida del beneficio.

El voucher responde a la pregunta:

- "qué voucher tiene hoy esta persona y en qué condiciones puede usarlo"

#### 1.3 Producto formativo

A nivel funcional, un producto formativo puede ser:

- carrera,
- curso.

Ambos deben compartir el mismo comportamiento frente a vouchers.

Cada producto formativo debería poder definir:

- si usa voucher,
- qué parametrías acepta,
- cuánto consume la inscripción en créditos.

El producto responde a la pregunta:

- "esta carrera o curso admite vouchers, cuáles, y cuánto consume"

#### 1.4 Comisión

La comisión no define política propia de voucher.

La comisión hereda la política del producto formativo padre.

Esto implica:

- una comisión de carrera usa la política de la carrera/oferta,
- una comisión de curso usa la política del curso.

La comisión responde a la pregunta:

- "en qué instancia operativa se aplica la misma política del producto"

#### 1.5 Consumo de voucher

El consumo es un movimiento auditable generado por una inscripción.

Debe registrar como mínimo:

- voucher utilizado,
- inscripción asociada,
- producto formativo,
- comisión,
- créditos consumidos,
- saldo anterior,
- saldo posterior,
- fecha,
- usuario o proceso,
- estado del movimiento.

El consumo responde a la pregunta:

- "cuándo, cómo y por qué se descontó crédito de un voucher"

## Reglas funcionales

### Regla 1. El producto acepta tipos de voucher, no vouchers individuales

Una carrera o curso no debe configurarse con vouchers concretos de ciudadanos.

Lo correcto es configurar parametrías o tipos de voucher aceptados.

Ejemplo correcto:

- la carrera A acepta voucher "Terminalidad Educativa"
- el curso B acepta voucher "Capacitación Laboral"

Ejemplo incorrecto:

- la carrera A usa el voucher individual #1542

### Regla 2. Si un producto usa voucher, debe tener parametrías permitidas

No debe existir un producto con:

- usa_voucher = verdadero
- sin parametrías configuradas

Ese estado debe tratarse como error de configuración.

### Regla 3. El único punto de consumo es la inscripción

La creación o edición de:

- carrera,
- curso,
- oferta,
- comisión,
- parametría,
- voucher del ciudadano,

no debe consumir crédito.

El descuento solo ocurre cuando una inscripción se confirma con voucher.

### Regla 4. La selección del voucher debe ser automática y explícita

El sistema debe buscar vouchers válidos del ciudadano y elegir uno según una
regla determinística.

La estrategia recomendada es:

1. obtener vouchers activos del ciudadano,
2. filtrar por parametrías permitidas por el producto,
3. filtrar por vigencia,
4. filtrar por saldo suficiente,
5. ordenar por fecha de vencimiento más próxima,
6. tomar el primero válido,
7. si uno falla, intentar con el siguiente,
8. rechazar solo si ninguno sirve.

### Regla 5. El costo en créditos debe tener una sola fuente de verdad

La solución recomendada es que el costo operativo en créditos lo defina el
producto formativo.

La parametría define elegibilidad y alcance; el producto define cuánto consume
la inscripción.

Esto evita aclaraciones ambiguas o costos implícitos hardcodeados.

### Regla 6. La anulación debe poder revertir el consumo

Si una inscripción consumió voucher y luego se anula, el sistema debe:

- identificar el movimiento aplicado,
- generar reversa,
- devolver créditos,
- dejar trazabilidad explícita.

No alcanza con volver a sumar saldo sin registrar el motivo.

### Regla 7. Carrera y curso deben comportarse igual

La lógica funcional de voucher no debe depender de si el producto es carrera o
curso, salvo que el negocio pida explícitamente reglas distintas.

La política esperada es homogénea.

## Flujo funcional esperado

### 1. Alta de parametría

1. se crea la parametría,
2. se define programa,
3. se define alcance,
4. se deja activa o inactiva,
5. queda disponible para configuración en productos.

### 2. Asignación de voucher al ciudadano

1. se elige ciudadano,
2. se elige parametría,
3. se define saldo inicial,
4. se define fecha de vencimiento,
5. se deja activo.

### 3. Configuración del producto formativo

1. se define si usa voucher,
2. se eligen parametrías permitidas,
3. se define costo en créditos,
4. la comisión hereda esta política.

### 4. Inscripción

1. se intenta inscribir al ciudadano,
2. si el producto no usa voucher, sigue el flujo normal,
3. si usa voucher, el sistema busca vouchers válidos,
4. si encuentra uno compatible, consume créditos,
5. registra el movimiento,
6. confirma la inscripción,
7. si no encuentra voucher válido, rechaza con motivo claro.

### 5. Anulación

1. se identifica el consumo previo,
2. se genera la reversa,
3. se actualiza el saldo,
4. se mantiene trazabilidad completa.

## Casos borde obligatorios

### Caso 1. El ciudadano tiene más de un voucher activo

Debe existir una regla explícita de selección. La recomendación es priorizar el
que vence antes.

### Caso 2. El primer voucher activo no sirve pero otro sí

El sistema no debe fallar al primer candidato inválido. Debe evaluar los demás
candidatos posibles.

### Caso 3. Tiene vouchers del programa pero no de la parametría permitida

La inscripción debe rechazarse.

### Caso 4. Tiene voucher correcto pero sin saldo suficiente

La inscripción debe rechazarse.

### Caso 5. El producto usa voucher pero no tiene parametrías configuradas

Debe tratarse como error de configuración del producto, no como ausencia de
voucher del ciudadano.

### Caso 6. Se intenta revertir una inscripción sin consumo previo

No debe generarse devolución ficticia.

### Caso 7. El voucher está activo pero vencido

No debe consumirse.

### Caso 8. Hay diferencias entre web y API

No debería existir lógica divergente de consumo según el canal. Ambos entrypoints
web y API deben usar el mismo criterio funcional.

## Mensajes funcionales esperados

### Errores del ciudadano

- no tiene vouchers activos para esta inscripción
- no tiene vouchers vigentes para esta inscripción
- no tiene créditos suficientes para esta inscripción
- no tiene vouchers compatibles con este producto

### Errores de configuración

- el producto usa vouchers pero no tiene parametrías configuradas
- el costo en créditos no está definido
- la parametría no aplica a este tipo de producto

### Mensajes de éxito

- inscripción confirmada con consumo de voucher
- voucher aplicado correctamente
- consumo revertido correctamente

## Alcance esperado por tipo de producto

### Carrera

Una carrera debe poder:

- indicar si usa voucher,
- aceptar una o varias parametrías,
- definir costo en créditos,
- delegar esa política a sus comisiones.

### Curso

Un curso debe poder:

- indicar si usa voucher,
- aceptar una o varias parametrías,
- definir costo en créditos,
- delegar esa política a sus comisiones.

### Comisión

La comisión:

- no define voucher propio,
- no elige parametrías propias,
- hereda las reglas del producto padre.

## Brechas detectadas contra la implementación actual

Este apartado resume el análisis técnico realizado sobre la rama actual.

### 1. Soporte parcial en carrera/oferta y ausencia en curso

Hoy la lógica de vouchers está modelada principalmente en oferta/carrera, pero
no en curso ni en comisión de curso. Esto deja incompleto el modelo funcional
si se pretende un comportamiento homogéneo.

### 2. Riesgo de consumo divergente entre canales

Se detectó riesgo de que la web y la API no utilicen exactamente la misma lógica
para seleccionar y consumir vouchers.

### 3. Selección insuficiente cuando hay múltiples vouchers activos

La estrategia actual puede fallar si toma un voucher inválido y no continúa con
otros candidatos potencialmente válidos.

### 4. Ambigüedad entre error del ciudadano y error de configuración

Si el producto usa voucher pero está mal configurado, el sistema no siempre
expresa ese problema como error del producto; en algunos flujos se degrada a un
error genérico del ciudadano.

### 5. Falta de definición operativa única para costo en créditos

Debe quedar explícito en una sola fuente de verdad para evitar descuentos
implícitos o inconsistentes entre productos.

## Consecuencias

### Positivas

- se unifica el criterio funcional para vouchers,
- se reduce ambigüedad entre negocio y desarrollo,
- se establece una base clara para corregir bugs actuales,
- se facilita documentar API, formularios, validaciones y testing.

### Trade-offs

- obliga a revisar implementaciones parciales actuales,
- probablemente requiera igualar el soporte de voucher entre carrera y curso,
- puede demandar ajustes en servicios de inscripción y en auditoría de
  movimientos.

## Lineamientos para implementación futura

1. Unificar el consumo de voucher en un único servicio reutilizable.
2. Evitar lógica divergente entre web, API y comandos.
3. Hacer explícita la diferencia entre parametría permitida y voucher individual.
4. Modelar soporte de voucher para curso si el negocio lo requiere realmente.
5. Garantizar reversa auditable de todo consumo.
6. Incorporar tests para:
   - múltiples vouchers activos,
   - voucher vencido pero activo,
   - producto mal configurado,
   - reversa de consumo,
   - consistencia entre web y API.

## Relación con documentación existente

- complementa `docs/vat/VOUCHER_SETUP.md`, que hoy describe principalmente
  configuración técnica y operativa;
- agrega la definición funcional y de negocio necesaria para seguir corrigiendo
  o extendiendo el módulo.

## Referencias

- `docs/vat/VOUCHER_SETUP.md`
- `VAT/models.py`
- `VAT/forms.py`
- `VAT/services/inscripcion_service.py`
- `VAT/api_views.py`
- `VAT/serializers.py`
