# El módulo se separa de la implementación, y las tablas cambian de prefijo

**Fecha:** 17 de septiembre de 2026
**Decide:** responsable funcional, con el equipo de desarrollo

---

## Qué se decidió

Que lo construido **no es RUNAC**: es un módulo reusable con RUNAC como primera
implementación.

```
MIR      Módulo de Importaciones Recurrentes. Nombre interno, del equipo.
RUNAC    una implementación. Hacia afuera, cada una lleva su propio nombre.
```

Y en consecuencia, que **las tablas pasan de `runac_*` a `mir_*`**: 56 tablas, y
las referencias en el código, los guiones SQL y las herramientas de análisis.

## Por qué ahora y no después

Porque el nombre de las tablas es de las pocas cosas que **no se pueden cambiar
después**. Las propias reglas de SISOC lo dicen: el nombre interno de la
aplicación se define una sola vez, «porque después no puede modificarse sin
renombrar todas sus tablas». Hacerlo antes de integrar cuesta una tarde;
hacerlo después cuesta una migración coordinada.

## Qué lo justificó, y cómo se verificó

El prefijo era **lo último que ataba el motor a RUNAC**. Antes de tocarlo se
midió: de las menciones a «runac» en el motor de importación, todas resultaron
ser nombres de tabla o comentarios. Se buscó lógica de negocio —MPI, MPE,
dispositivos, niño, medida de protección— y lo único que apareció fue un ejemplo
dentro de un comentario.

Es decir que **«el motor no sabe qué es una MPI» dejó de ser una afirmación de
diseño y pasó a ser una propiedad verificable**. Esa es la razón por la que el
renombre valía la pena: no es cosmética, es lo que hace cierta la reusabilidad.

## Qué NO se tocó, deliberadamente

**36 índices y 28 claves foráneas conservan el nombre viejo.** Son
identificadores internos: no aparecen en ninguna consulta, ni en el código, ni en
las pantallas. Renombrarlos agrega riesgo —una clave foránea mal renombrada rompe
la integridad referencial de verdad, no el nombre— sin ninguna ganancia. Queda
escrito para que nadie lo lea como un trabajo a medio hacer.

## Lo que esto abre, y hay que decidir antes de integrar

Hoy, fuera del repositorio, **cada implementación tiene su propia base de
datos**. SISOC es una sola base.

Al integrar, las implementaciones dejan de separarse por base y tienen que
separarse por dato: una columna que diga a qué implementación pertenece cada
archivo, cada período y cada presentación. No es difícil, pero cambia el modelo y
conviene resolverlo antes de escribir las migraciones.

Está desarrollado en [03-arquitectura.md](../03-arquitectura.md).

## La pieza que falta

Un **administrador de instancias**: algo que sepa qué implementaciones existen,
sus datos de conexión, y qué tableros y funcionalidades se habilitan a cada una.
No se construyó a propósito —la prioridad es que RUNAC funcione— pero las dos
condiciones para que siga siendo posible ya se cumplen:

1. cada implementación tiene su definición y sus datos separados;
2. el motor no tiene lógica de ninguna implementación en particular.

---

## En el mismo tramo

Tres decisiones menores que salieron de usar el sistema y conviene que queden
registradas:

**`HORA` es el quinto tipo de dato.** Antes había cuatro —texto, entero, decimal
y fecha— y las horas se guardaban como fecha. El propio extractor tenía escrito
en un comentario «el modelo no tiene tipo HORA; se guarda como texto». Ahora
existe.

**El repositorio del sistema se clona y se levanta con dos comandos.** Antes
tenía la aplicación pero no la base ni cómo armarla, así que las correcciones de
la definición vivían en un solo disco. Hoy viajan con el código.

**Las reglas y los tipos se corrigieron contra lo que dice la propia planilla.**
Diez campos que cuentan cosas estaban declarados como texto —y por eso admitían
veintiocho dígitos sin una queja— y siete estaban declarados como fecha sin
serlo. En ambos casos la corrección no salió de una opinión del equipo: las
hojas de categorías de la planilla de la DNPYPI ya declaraban el tipo correcto y
nadie las estaba leyendo. Ver
[08-analisis-de-las-planillas.md](../08-analisis-de-las-planillas.md).
