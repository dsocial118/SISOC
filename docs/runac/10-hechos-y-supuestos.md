# Hechos, supuestos y jerarquía de fuentes

**Verificado el 17 de septiembre de 2026.**

Este documento separa tres cosas que en el resto de la carpeta aparecen
mezcladas: **lo que la DNPYPI confirmó**, **lo que supuso el equipo técnico**, y
**qué fuente le gana a cuál** cuando dos se contradicen.

No es burocracia. Casi todo lo que hoy hace el sistema —las 156 reglas, los
límites numéricos, qué bloquea y qué avisa— **son supuestos nuestros**, y quien
lea la documentación sin este documento no tiene forma de distinguirlos de una
definición institucional.

---

## 1. Qué fuente le gana a cuál

Cuando dos fuentes dicen cosas distintas sobre el mismo campo, gana la de número
más bajo:

| | Fuente | Ejemplo |
|:---:|---|---|
| **1** | **Definición explícita de la DNPYPI**, escrita y con fecha | Una respuesta a una consulta, un correo, un acta |
| **2** | **El requerimiento del área** | El documento funcional original y el apartado técnico |
| **3** | **Lo que la planilla declara sobre sí misma** | Las hojas de categorías, la fila que marca los obligatorios, las listas desplegables, la fila de anotaciones |
| **4** | **Los datos y el formato de celda** | Lo que efectivamente vino informado en las presentaciones |
| **5** | **La inferencia del sistema** | El tipo que `inferir.py` deduce del nombre del campo |
| **6** | **El criterio del equipo técnico** | Todo lo demás |

### La regla que más caro nos salió

> **El nivel 3 le gana al nivel 5.** Lo que la planilla declara sobre sí misma
> vence a lo que el sistema infiere del nombre del campo.

Parece obvio escrito así. En la práctica estuvo al revés durante semanas: diez
campos que cuentan cosas quedaron declarados TEXTO —y por eso admitían veintiocho
dígitos sin una queja— y siete quedaron declarados FECHA sin serlo. **Las hojas
de categorías de la planilla ya declaraban el tipo correcto y nadie las estaba
leyendo.** Se corrigió el 16 de septiembre.

### Y el corolario

> **El nivel 4 no le gana a nada por sí solo.** Que un dato haya venido de cierta
> forma no prueba que esté bien: puede ser el error que el sistema tiene que
> detectar.

---

## 2. Hechos confirmados

Lo que sí está definido. Cada uno con su origen, para poder volver a chequearlo.

### Del requerimiento del área

- El registro **vive dentro de SISOC**, no es un sistema aparte.
- Las provincias presentan **trimestralmente**.
- Se reciben **cinco archivos**: MPI, MPE, MPJ+DAE en un mismo libro, y dos de
  dispositivos —penal y cuidado residencial—.
- Hay que **conservar el historial** y saber de dónde vino cada dato: provincia,
  período, archivo, hoja, fila y versión.
- Los archivos se cargan **sin modificar su estructura básica**.
- Hace falta **revisión nacional y subsanación provincial**: la provincia corrige
  lo suyo, la Nación revisa.
- **No debe pensarse como una planilla en línea.**

### De las planillas, verificado el 17 de septiembre contra la definición cargada

- **365 columnas** en **10 hojas** de datos, de las cuales **31 son
  obligatorias** — la planilla lo declara en su primera fila.
- **93 catálogos** con **797 opciones**, tomados de las listas desplegables y de
  las hojas de categorías.
- El legajo del niño trae un nomenclador de **13.521 localidades** de las 24
  provincias, y la columna `Provincia` declara que hay que usar el clasificador
  **BAHRA**.

### De la entrega del 10 y 11 de septiembre

- El **legajo del niño se separó** de las nóminas, y el **MPE corregido lo
  referencia**. Es el cambio que destrabó el rediseño.
- **Faltan MPI, MPJ y DAE corregidos** con el mismo criterio.

---

## 3. Supuestos vigentes

**Nada de lo que sigue fue validado por la DNPYPI.** Está escrito para que
tengan algo concreto que corregir, no para que se aplique tal cual.

La ventaja, y es la razón de todo el diseño: **cambiar un supuesto es cambiar un
dato, no reprogramar**. Donde dice «entre 0 y 17», si son 12 a 17 se cambian dos
números en una fila de la base.

| # | Supuesto | De dónde salió | Qué pasa si está mal |
|:---:|---|---|---|
| S-1 | **Las 156 reglas de validación**, una por una | Del nombre de los campos, del apartado técnico y de la estructura de las planillas | Se corrige regla por regla, sin tocar código |
| S-2 | **La severidad de cada regla**: 84 avisan, 72 bloquean | Criterio del equipo. `07-reglas-de-validacion.md` lo declara como entregable aparte | Una regla mal puesta como bloqueante **frena una presentación entera** |
| S-3 | **Los límites numéricos concretos**: edades, cantidades, capacidades | Inventados para que la regla exista | Datos buenos rechazados, o datos malos aceptados |
| S-4 | **Los tipos de dato de los campos que la planilla no declara** | `inferir.py`, por el nombre del campo. Cada uno lleva un nivel de confianza | Un tipo mal puesto **rechaza datos correctos**: es la clase de defecto más grave |
| S-5 | **El nombre de los 93 catálogos** | Inventados por nosotros donde la planilla traía una lista suelta | Sólo estética, salvo que dos catálogos iguales queden con nombres distintos |
| S-6 | **Qué campos son normalizables, y en qué alcance** | Hoy los 365 arrancan en `SIN_NORMALIZAR` | Trabajo de normalización que no se hace, o que se hace sobre el campo equivocado |
| S-7 | **Que las hojas de categorías declaran el tipo de cada campo** | Lectura nuestra de la planilla. **Ya se aplicó**: corrigió 10 campos a ENTERO y 7 que no eran fechas | Si la lectura es incorrecta, hay 17 campos mal tipados hoy |
| S-8 | **Que BAHRA es el nomenclador territorial** | Lo declara la columna `Provincia` del legajo, pero no está confirmado a qué nivel se informa | Todo el modelo del legajo. Consulta 1 |
| S-9 | **Que el nomenclador se carga una vez en el sistema** y las provincias eligen de él | Propuesta nuestra | Si se toma como hoja de datos, a cada provincia se le piden **13.521 filas** |
| S-10 | **Que si la cabecera del archivo dice una provincia y en pantalla se eligió otra, se rechaza la carga** | Propuesta nuestra. La alternativa —que mande la cabecera— es igual de válida | Cambia si la pantalla sigue pidiendo provincia y período |
| S-11 | **Que el legajo es la fuente de identidad**, y por lo tanto si falla traba la presentación entera | Consecuencia derivada del rediseño, no una decisión tomada | Cambia la experiencia de quien carga, no el modelo |
| S-12 | **El orden de importación de los archivos** | Criterio nuestro, apoyado en las dependencias entre archivos | Se reordena: es configuración |

### Los tres que más conviene cerrar primero

**S-2 y S-3 van juntos** y son los que más duelen: una regla con el límite
equivocado *y* marcada como bloqueante rechaza una presentación válida. Es el
peor resultado posible del sistema —peor que no validar nada, porque genera
trabajo y desconfianza—.

**S-7 ya está aplicado.** Es el único supuesto de esta lista que no está
esperando: se tomó una decisión y se corrigieron 17 campos con ella. Si la
lectura de las hojas de categorías es incorrecta, hay que revertirlo.

---

## 4. Lo que está sin respuesta

Las consultas abiertas a la DNPYPI se mantienen en el documento de trabajo
`09_Consultas_a_la_DNPYPI.md`, separadas por si frenan el trabajo o no.

Las definiciones pendientes que dependen de la coordinación de SISOC —RENAPER,
seguridad social, nomenclador territorial, alta de ciudadanos— están en
[03-arquitectura.md](03-arquitectura.md).

Las decisiones técnicas pendientes están en [decisiones/](decisiones/).

---

## 5. Cómo se mantiene esto

Un supuesto se mueve a **hecho confirmado** cuando hay una definición escrita y
fechada de la DNPYPI, y se anota de dónde salió. No por inferencia, y no porque
lleve mucho tiempo sin que nadie lo discuta.

> **Un supuesto que nadie objetó sigue siendo un supuesto.** El silencio no
> confirma.
