# Reglas de validación

Las validaciones deben informarse **con lenguaje claro**: el usuario tiene que
saber exactamente qué archivo, hoja, fila y campo debe corregir.

---

## Los tres tipos de resultado

| Tipo | Ejemplos | Efecto |
|---|---|---|
| **Error bloqueante** | Archivo incorrecto; columna faltante; documento o fecha con formato inválido; fecha de egreso anterior al ingreso; dispositivo obligatorio no encontrado; duplicado exacto | **Impide la importación completa del archivo.** Se corrige en el Excel y se vuelve a importar |
| **Advertencia** | Dato opcional vacío; cambio muy alto respecto del trimestre anterior; edad o permanencia atípica; posible duplicado | Permite continuar. Se resuelve dentro del sistema, editando el dato o justificándolo |
| **Control de catálogo** | Valor que no coincide con los desplegables de provincia, género, modalidad, tipo de dispositivo, situación procesal u otras categorías | Solicita corregir o mapear el valor provincial |

**Controles prioritarios**, del requerimiento:

- campos obligatorios y formatos de fecha, hora, documento y números;
- coherencia entre fecha de nacimiento, edad, ingreso, egreso e inicio o cese de
  medida;
- posibles personas duplicadas por documento, CUIL, nombre, fecha de nacimiento e
  identificador provincial;
- posibles dispositivos duplicados por nombre, tipo, localidad y dependencia;
- vínculo válido entre MPE y dispositivo residencial, y entre MPJ/DAE y
  dispositivo penal;
- diferencias relevantes respecto de la presentación anterior;
- **filas vacías entre registros completos**: se consideran error y deben
  corregirse antes de importar.

> **Definición pendiente.** Definir con precisión cuáles de estos controles son
> advertencia y cuáles bloqueante. La matriz completa, campo por campo, es un
> entregable aparte.

---

## Cómo se declaran

Las reglas **no se programan: se declaran**. Cada regla es la aplicación de un
**tipo de regla** a uno o más campos, con sus parámetros.

Cada regla aplicada se define por cinco elementos:

| Elemento | Ejemplo |
|---|---|
| Tipo de regla | Comparar campo |
| Campo o campos | Fecha de finalización de la medida |
| Parámetros | Comparar con *Fecha de inicio*, operador *mayor o igual* |
| Severidad | Bloqueante |
| Mensaje al usuario | *"La fecha de finalización no puede ser anterior a la de inicio."* |

**La severidad es atributo de la regla aplicada, no del tipo.** Un mismo tipo
puede ser bloqueante en un campo y advertencia en otro.

**El mensaje al usuario forma parte de la definición y no del programa.** Al
residir en la definición, puede ajustarse para hacerlo más comprensible sin
intervención de desarrollo.

**Los tipos constituyen un vocabulario genérico.** Verificar que un valor esté
dentro de un rango, que coincida con un formato, que no se repita, que sea
obligatorio cuando otro campo toma determinado valor o que guarde relación con
otro campo del mismo registro son necesidades comunes a cualquier proceso de
validación. Un relevamiento distinto usa los mismos tipos con otros parámetros.

En consecuencia, **modificar una regla, cambiar su severidad o mejorar su mensaje
no requiere desarrollo**: se resuelve desde la administración del sistema.

---

## Tipos de regla

Las reglas pueden reutilizarse y aplicarse a uno o más campos. Cada tipo
determina los parámetros necesarios y los operadores que admite.

| Tipo | Descripción | Parámetros | Operadores | Ejemplo |
|---|---|---|---|---|
| **RANGO** | El valor se encuentra entre un mínimo y un máximo | minimo, maximo | — | La capacidad declarada debe estar entre 1 y 200 |
| **COMPARAR_VALOR** | Compara el campo con un valor determinado | operador, valor | IGUAL, DISTINTO, MAYOR, MAYOR_IGUAL, MENOR, MENOR_IGUAL, EN_LISTA, NO_EN_LISTA | El año debe ser mayor o igual a 2020 |
| **OBLIGATORIO_SI** | El campo es obligatorio cuando otro cumple una condición | campo_condicion, operador, valor_condicion | IGUAL, DISTINTO, ES_VACIO, NO_ES_VACIO, EN_LISTA, NO_EN_LISTA | *Descripción de otros* es obligatoria cuando *Tipo de respuesta* es OTROS |
| **COMPARAR_CAMPO** | Compara con otro campo del mismo registro | campo_comparacion, operador | IGUAL, DISTINTO, MAYOR, MAYOR_IGUAL, MENOR, MENOR_IGUAL | La fecha de finalización debe ser posterior o igual a la de inicio |
| **FORMATO** | El contenido respeta un formato | formato | — | El valor debe respetar el formato de CUIL |
| **UNICO_EN_HOJA** | El valor no se repite dentro de la hoja | — | — | El identificador provincial no puede repetirse |
| **UNICO_COMBINADO** | No se repite una combinación de campos | campos_combinados | — | No puede repetirse tipo y número de documento con fecha de inicio |
| **EXISTE_EN** | El valor corresponde a un registro existente en otro conjunto ya cargado | conjunto, campo_destino, ambito | — | El nombre del dispositivo debe corresponder a uno cargado por la jurisdicción |
| **EJECUTAR_FUNCION** | Ejecuta una función de validación implementada y habilitada en SISOC | funcion | — | Verificar que un CUIL o un correo sean válidos |

`EJECUTAR_FUNCION` está destinado a validaciones que no pueden expresarse
mediante parámetros. Su alcance se limita a funciones previamente implementadas:
**no es una vía para incorporar lógica específica por fuera de la definición**,
sino un conjunto acotado de verificaciones reutilizables.

<!-- COMENTARIO: EXISTE_EN se incorporó al analizar la vinculación entre medidas
     y dispositivos. Sin ese tipo, la propuesta del apartado 2 de
     08-analisis-de-las-planillas.md no tiene cómo implementarse. El parámetro
     `ambito` es el que evita que una provincia referencie un dispositivo de
     otra. -->

---

## Validaciones intrínsecas del campo

Además de las reglas, cada campo tiene validaciones que surgen de su propia
definición en la Capa 1 y no requieren declararse:

- **tipo de dato**: lo que se declaró como fecha tiene que ser una fecha;
- **obligatoriedad**;
- **valor de catálogo**: si el campo tiene lista cerrada, el valor debe estar en
  ella;
- **longitud máxima**.

Se informan igual que las reglas —con su fila, columna, valor y motivo— pero no
tienen una regla asociada: el código del incumplimiento indica de cuál se trata.

---

## Lo que falta definir

> **Reglas contra la base consolidada.** Resta definir las reglas que comparan un
> campo con información de períodos anteriores: detección de variaciones
> significativas respecto del corte previo, o identificación de posibles errores
> de tipeo en el documento a partir del resto de los datos de la persona. Al no
> existir todavía una base previa, su definición puede posponerse sin afectar la
> primera versión.

> **Error de tipeo en el documento.** Un documento puede llegar mal escrito. Se
> propone detectarlo comparando el resto de los datos —nombre, apellido y fecha
> de nacimiento— contra presentaciones anteriores y contra RENAPER. Corresponde
> definir qué hace el sistema ante una coincidencia parcial: si bloquea, si
> advierte, o si registra y lo deja para revisión.

---

## Quién las escribe, y dónde se consultan

Las reglas **las define la DNPYPI**, no el equipo de desarrollo. Es la única
instancia que sabe qué debe cumplir cada dato: si la fecha de egreso obliga a
informar el destino, si el CUIL debe verificarse, si una medida no puede iniciar
después de la fecha del relevamiento.

Para eso el documento de revisión de campos que se trabaja con la contraparte
incluye una columna **«Reglas»** donde cada condición se escribe en castellano.
Lo que se escriba ahí se traduce a una regla declarada y el sistema la controla
al importar.

Del otro lado, el operador provincial cuenta con una pantalla de consulta que
muestra, **por archivo y hoja**, qué se espera de cada columna:

| Col. | Campo | Oblig. | Qué se espera | Valores admitidos | Condiciones |
|---|---|---|---|---|---|
| N | Cuenta con protocolos de ingreso | — | Una opción de la lista | Sí · No · Sin datos | — |
| AF | Fecha de inicio MPE | Sí | Fecha | | No puede ser posterior a la del relevamiento |

Sin nombres técnicos y con el tipo de dato dicho en castellano —*Fecha*, *Número
entero*, *Texto, hasta 120 caracteres*—. Las listas de más de ocho opciones se
nombran en lugar de enumerarse: *Provincias válidas (25)*, *Países válidos (246)*.

El propósito es que quien completa la planilla **no tenga que adivinar** qué va
en cada columna, y que cada regla que la DNPYPI defina se vuelva visible para
quien tiene que cumplirla.

---

## Estado

Cargadas y verificadas sobre los cinco archivos entregados: **368 campos, 81
catálogos, 708 opciones** y las reglas identificadas hasta el momento.

Las reglas concretas que hoy sugiere el análisis automático son **tentativas**:
deben modelarse contra la realidad de cada archivo, no darse por buenas.

<!-- COMENTARIO: de los 368 campos, sólo 62 tienen hoy una regla declarada. La
     enorme mayoría de las validaciones son intrínsecas —tipo, obligatoriedad,
     pertenencia a un catálogo— y no requieren regla. Es esperable que la
     columna de condiciones esté vacía en la mayor parte de las columnas. -->
