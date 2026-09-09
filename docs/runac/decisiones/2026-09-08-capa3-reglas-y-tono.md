# 2026-09-08 — Capa 3, consulta de reglas y criterio de tono

## Capa 3: la identidad se separa de lo relevado

**Decisión.** `runac_c3_persona` guarda **sólo la identidad resuelta** —documento,
CUIL, vínculo con `ciudadanos`—. Todo lo que las planillas relevan sobre alguien
vive en su caracterización: `nino_adolescente` o `referente_adulto`.

**Motivo.** Un hermano mayor puede ser a la vez referente de su hermano menor y
estar alcanzado por una medida propia. Es una sola persona con dos
caracterizaciones. Con los datos de identidad repartidos dentro de cada una,
quedaría registrada dos veces sin forma de saber que es la misma.

**Además:** una tabla de medida por tipo y no una genérica, porque su contenido no
es comparable; identificación común de dispositivo más una tabla por tipo;
`disp_alcance_territorial` como relación, porque MPT, CAD y guardia informan
varias jurisdicciones; y cuatro tablas de trazabilidad, de las cuales `cambio`
**no es auditoría sino la fuente de las series históricas**, porque la base
guarda una sola fila por chico con el dato vigente.

El esquema quedó en **23 tablas y 45 claves foráneas**, creado y sin datos.

---

## Consulta de qué se espera en cada columna

**Decisión.** El operador provincial cuenta con una pantalla que muestra, por
archivo y hoja, qué va en cada columna: si es obligatoria, qué tipo de dato
admite, qué valores acepta y qué condiciones debe cumplir.

**Motivo.** Sin eso, quien completa la planilla tiene que adivinar. Y del otro
lado, cada regla que la DNPYPI defina necesita volverse visible para quien tiene
que cumplirla, o no sirve de nada haberla declarado.

**Criterios de armado**, que conviene no perder al modificarla:

- **Se elige archivo y hoja.** Un archivo con seis hojas volcadas una debajo de
  la otra no se consulta.
- **Sin contadores.** Cuántas listas tiene un archivo no le sirve a quien está
  por completarlo.
- **Sin nombres técnicos**, salvo para el administrador.
- **El tipo de dato en castellano**: *Texto, hasta 120 caracteres*, no
  `TEXTO(120)`.
- **Las listas de más de ocho opciones se nombran, no se enumeran**: *Países
  válidos (246)*.

---

## Los títulos se componen con su grupo

**Problema.** Varias planillas ponen el principio de la pregunta en una celda
combinada —*«El establecimiento cuenta con…»*— y en cada columna sólo la
continuación. Leídas de a una quedan como *«… reglamento de convivencia?»*.

**No es un error de la planilla**: para una persona que mira el Excel se lee
perfecto, porque ve las dos filas juntas. El problema aparece al leer columna por
columna.

**Decisión.** El título se recompone juntando la dimensión con el texto de la
columna. Resuelve de una vez los tres lugares donde aparecía cortado: la
plantilla generada, la pantalla de edición y los mensajes de error.

---

## Criterio de tono para lo que se comparte con la DNPYPI

**Decisión del responsable funcional, y aplica a todo el material que ellos ven.**
No es una auditoría: es una ayuda para que confirmen sin escribir desde cero. Los
expertos en el contenido son ellos.

De ahí cuatro reglas:

1. **Se marca como error sólo lo que es un error de verdad**, y error es que la
   lista desplegable no corresponda al campo. En 368 columnas hay **una sola**.
2. **Los textos son cortos.** Una observación de cinco renglones no se lee.
3. **Lo que se repite va como nota al pie**, una vez por hoja.
4. **Las diferencias entre listas que deberían ser idénticas no van en el
   documento compartido.** Son equivocaciones, no errores de criterio, y
   señalarlas por escrito queda pedante. Van aparte, para conversarlas.

---

## Sobre los mensajes del sistema

**Impersonal, no *usted*.** Es lo estándar en administración pública y evita el
problema de tutear o ustedear a alguien que no se conoce:

> *DISP_SCP: se detectaron 8 errores bloqueantes. No se incorporó ningún registro
> de este archivo. Hay que corregir el Excel y volver a importarlo.*

Y **los mensajes nombran las columnas por su título**, no por el nombre técnico
con que las guarda la base: *«¿Se identifica con algún pueblo originario?»*, no
`se_identifica_con_algun_pueblo_originario`.

---

## Hallazgo con efecto sobre el orden de carga

Un archivo **cuenta como importado sólo si su importación quedó válida**. Una
importación fallida no destraba a los archivos siguientes.

Es correcto —una nómina no puede referenciar dispositivos que no entraron— pero
conviene tenerlo presente: si el primer archivo del orden falla, no se puede
avanzar con ninguno hasta corregirlo.
