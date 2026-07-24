# Guía de onboarding - Módulo INET (VAT)
## Alta de cursos y comisiones completas

## Alcance

Esta guía cubre exclusivamente el flujo de **alta de un curso** y **alta de una comisión completa** dentro de un Centro, tal como funciona hoy en la interfaz web del módulo INET (app `VAT`). No cubre configuración de centros, planes curriculares, inscripciones ni asistencia.

> Nota técnica: el sistema tiene dos capas de datos para "curso/comisión". Esta guía documenta la capa **operativa actual** (`Curso` / `ComisionCurso`), que es la que se usa desde el panel de un Centro. Existe una capa anterior ("Fase 4", `OfertaInstitucional` / `Comision`) que ya no es el camino de alta disponible en pantalla.

## ¿Quién puede dar de alta cursos y comisiones?

- El grupo **CFP** (referente de centro) es quien opera este flujo: debe estar asignado como referente del Centro puntual donde va a crear el curso/comisión.
- El grupo **CFPINET** (acceso total) también puede hacerlo en cualquier centro.
- El grupo **CFPJuridicccion** (provincial) puede crear y editar Centros, pero no tiene habilitada la carga de cursos ni comisiones.
- Los roles de solo lectura (revisor de centro, INET Admin Visualizador) no pueden dar de alta nada.

Si no ves los botones "Agregar curso" o "Comisión" descriptos más abajo, lo más probable es que no tengas el permiso correspondiente o no estés cargado como referente de ese Centro.

## Requisitos previos

Antes de empezar, verificar que:
- el Centro ya exista en el sistema,
- el Plan Curricular que vas a usar ya esté cargado para la provincia del Centro,
- si el curso va a usar vouchers, que los vouchers del programa ya existan,
- estés parado dentro del Centro correcto (todo lo que cargues queda asociado a ese Centro).

## 1. Ingresar al panel de cursos del Centro

1. Entrar al detalle del **Centro** correspondiente.
2. Ir a la pestaña **"Cursos"** dentro del detalle del Centro.
3. Se cargan dos secciones: **"Oferta educativa"** (tabla de cursos) y **"Comisiones"** (tabla de comisiones).

## 2. Alta de un curso

### Pasos

1. En la sección "Oferta educativa", hacer clic en **"Agregar curso"**.
2. Completar el formulario (los campos aparecen en este orden):

| Campo | Obligatorio | Detalle |
|---|---|---|
| Plan de Estudio | Sí | Se filtra automáticamente a los planes de la provincia del Centro. Al elegirlo, el sistema define solo la **modalidad de cursada** del curso (presencial/virtual/mixta) — no se elige a mano. |
| Nombre | Sí | Nombre del curso, hasta 255 caracteres. |
| Tipo | No | Puede seleccionarse uno o varios valores. |
| Estado | Sí | Planificado (valor inicial habitual), Activo, Finalizado o Cancelado. |
| Usa Voucher | No | Casillero. No puede activarse junto con "Inscripción libre". |
| Inscripción libre | No | Casillero. No puede activarse junto con "Usa Voucher". |
| Vouchers | Solo si "Usa Voucher" está tildado | Deben pertenecer todos al mismo programa. |
| Costo en créditos | Solo si "Usa Voucher" está tildado | Debe ser mayor a 0 si usa voucher; si no usa voucher, el sistema lo deja en 0 automáticamente. |
| Observaciones | No | Texto libre. |

3. Hacer clic en **Guardar**.

El Centro y la modalidad del curso se completan automáticamente por el sistema, no hay que cargarlos.

### Recomendaciones

- Confirmar que el Plan de Estudio elegido sea el correcto: de él depende la modalidad del curso.
- Si el curso no va a usar vouchers ni inscripción libre, dejar ambas opciones sin marcar.
- Un curso "eliminado" no se borra físicamente: pasa a estado **Cancelado**.

## 3. Alta de una comisión completa

Una comisión se considera **completa** cuando fue cargada con toda su información básica válida **y al menos un horario de clase** que cumpla las reglas de duración detalladas más abajo. El único camino disponible en pantalla para dar de alta una comisión es un **wizard de 3 pasos**; no existe un botón para crear una comisión "vacía" sin horarios.

### Cómo empezar

1. En la tabla "Oferta educativa", ubicar el curso ya creado.
2. Hacer clic en el botón **"Comisión"** de la fila de ese curso. Esto abre el wizard **"Nueva Comisión de curso"**.

### Paso 1 del wizard — Información básica

| Campo | Obligatorio | Detalle |
|---|---|---|
| Curso | — | Solo informativo, ya viene definido. |
| Ubicación | Sí | Debe ser una ubicación del mismo Centro del curso. |
| Cupo total | Sí | Debe estar **entre 5 y 100** estudiantes. |
| Estado | Sí | Planificada (valor inicial habitual), Activa, Cerrada o Suspendida. |
| Fecha de inicio | Sí | Debe ser **hoy o una fecha posterior**. |
| Fecha de finalización | Sí | Debe ser **posterior** a la fecha de inicio (no puede ser la misma fecha). |
| Acepta lista de espera | No | Casillero. |
| Cupo de lista de espera | Solo si "Acepta lista de espera" está tildado | — |
| Observaciones | No | Texto libre. |

El código de comisión y el nombre de la comisión se generan automáticamente por el sistema; no se piden en el formulario.

### Paso 2 del wizard — Horarios

Se carga una tabla de horarios (Día de la semana, Hora de inicio, Hora de finalización, Estado Activo/Inactivo). Reglas que hay que cumplir para poder avanzar:

- **Al menos 1 horario** es obligatorio.
- Cada clase debe durar **entre 45 minutos y 4 horas**.
- El **total semanal** de horas debe ser de **al menos 2 horas**.
- **No puede repetirse** el mismo día de la semana en dos filas.

Si alguna de estas reglas no se cumple, el sistema no deja avanzar al paso 3.

### Paso 3 del wizard — Confirmación

1. Revisar el resumen: datos del curso, datos de la comisión y horarios cargados con su duración total.
2. Hacer clic en **"Confirmar y crear comisión"**.

Al confirmar, el sistema:
- crea la comisión,
- crea los horarios cargados,
- genera automáticamente las sesiones de clase concretas para todo el período entre la fecha de inicio y la fecha de fin, según los días y horarios definidos.

Después de confirmar, se vuelve al detalle del Centro y la comisión ya aparece en la tabla "Comisiones".

## 4. Agregar o editar un horario después de creada la comisión

Desde el detalle de la comisión ya creada se pueden agregar o editar horarios sueltos. Importante: esta pantalla **no aplica** las reglas estrictas del wizard (45 min–4 hs, sin días repetidos, mínimo semanal de 2 hs) — solo valida que la hora de fin no sea anterior a la de inicio y que no se repita el mismo día y horario. Al guardar, el sistema regenera las sesiones de clase correspondientes.

## 5. Validación final

Después de guardar, verificar que:
- la comisión aparece en la tabla "Comisiones" del Centro,
- el estado de la comisión es el esperado,
- las fechas y el cupo son correctos,
- si corresponde, la lista de espera y su cupo están bien configurados.

## 6. Buenas prácticas

- Verificar siempre que se está trabajando dentro del Centro correcto antes de crear curso o comisión.
- Elegir con cuidado el Plan de Estudio del curso: de él depende la modalidad y no se puede elegir manualmente.
- No usar "Usa Voucher" e "Inscripción libre" a la vez: son mutuamente excluyentes.
- Cargar los horarios respetando los límites (45 min–4 hs por clase, mínimo 2 hs semanales, sin días repetidos) para que la comisión quede completa en un solo paso.
- Recordar que "eliminar" un curso o una comisión no los borra: los pasa a estado Cancelado / Cerrada.

## 7. Resumen rápido

1. Entrar al Centro → pestaña "Cursos".
2. "Agregar curso" → completar Plan de Estudio, Nombre, Estado (y Vouchers/Inscripción libre si corresponde) → Guardar.
3. En la fila del curso, botón "Comisión" → wizard:
   - Paso 1: Ubicación, Cupo (5–100), Estado, Fechas, Lista de espera.
   - Paso 2: al menos 1 horario válido (45 min–4 hs, sin días repetidos, mínimo 2 hs semanales).
   - Paso 3: revisar resumen → "Confirmar y crear comisión".
4. La comisión queda visible en la tabla "Comisiones" del Centro, con sus sesiones de clase ya generadas.

## 8. Preguntas frecuentes

**¿Por qué no veo el botón "Agregar curso" o "Comisión"?**
Falta el permiso correspondiente o no estás asignado como referente de ese Centro. Consultar con un administrador (grupo CFPINET).

**¿Por qué no puedo elegir la modalidad del curso?**
La modalidad se toma automáticamente del Plan de Estudio seleccionado; no es un campo editable.

**¿Por qué el wizard no me deja avanzar del paso de horarios?**
Revisar que haya al menos un horario cargado, que cada clase dure entre 45 minutos y 4 horas, que el total semanal sea de al menos 2 horas, y que no haya dos horarios en el mismo día.

**¿Por qué la fecha de inicio de la comisión me da error?**
La fecha de inicio no puede ser anterior al día de hoy, y la fecha de fin tiene que ser posterior a la de inicio (no puede coincidir).

**¿Qué pasa si "elimino" un curso o una comisión?**
No se borran: el curso pasa a estado Cancelado y la comisión a estado Cerrada.
