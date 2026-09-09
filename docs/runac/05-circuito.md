# Circuito de carga, revisión y presentación

Nueve pasos, de la carga provincial a la consolidación nacional. El criterio es
que reduzca la edición manual y **mantenga la responsabilidad provincial sobre
los datos**: el nivel nacional revisa y observa, no corrige.

---

## Vocabulario

Estos términos significan cosas distintas y no son intercambiables. La confusión
entre *importación* y *presentación* fue lo que motivó fijarlos por escrito.

| Término | Qué es |
|---|---|
| **Importación** | El sistema no encontró errores bloqueantes y la información fue incorporada a la Capa 2 |
| **Edición** | Corrección de un dato en la Capa 2, cuando la información ya fue importada |
| **Cierre de carga** | El responsable provincial declara terminada la carga del período y la envía a revisión nacional |
| **Observación** | Aclaraciones y dudas del revisor técnico nacional sobre los datos cargados |
| **Presentación** | El acto formal por el cual la provincia declara que esos son los datos del período, una vez que el revisor resolvió sus observaciones y habilitó la opción. Genera un comprobante para remitir por GDE |
| **Consolidación** | Incorporación de los datos de la Capa 2 a la base consolidada de la Capa 3 |

---

## Los nueve pasos

| Acción | Actor | Responsabilidades |
|---|---|---|
| **1. Carga de dispositivos.** La provincia carga primero las bases de dispositivos residenciales y penales. SISOC valida y asigna los ID de dispositivo. | Operador provincial | Cargar archivos, consultar errores y preparar correcciones. |
| **2. Carga de nóminas.** La provincia carga MPI, MPE, MPJ y DAE. El sistema identifica personas, medidas y relaciones con dispositivos. | Operador provincial | Ídem. Los dispositivos deben estar cargados antes que las nóminas que los referencian. |
| **3. Control de admisión.** SISOC verifica que el archivo coincida con la plantilla vigente: nombre de las hojas, nombre y orden de las columnas. Si no coincide, no se importa ningún registro y el archivo vuelve al operador. | SISOC | Rechazar el archivo e indicar qué no coincide. |
| **4. Validación de datos.** Sobre los archivos admitidos, SISOC controla campos obligatorios, tipos, fechas, catálogos, duplicados y relaciones. **Si detecta errores bloqueantes, no se importa ningún registro** y emite el informe. Si no los hay, la información se incorpora a la Capa 2. | SISOC | Informar por archivo, hoja, fila, columna y motivo. |
| **5. Corrección.** Los errores **bloqueantes** se corrigen en el Excel y el archivo se vuelve a importar. Las **advertencias** se resuelven dentro del sistema, editando el dato o justificándolo. | Operador provincial | Corregir. Toda edición queda registrada con usuario, fecha, valor anterior y valor nuevo. |
| **6. Cierre de carga.** El responsable provincial declara terminada la carga del período y la envía a revisión nacional. | Responsable provincial | Revisar lo cargado por el operador y decidir cuándo está en condiciones de revisarse. |
| **7. Revisión nacional.** El revisor formula observaciones sin modificar los datos provinciales. Si hay observaciones, la carga vuelve a la provincia; si no las hay, habilita la presentación. | Revisor técnico nacional | Revisar calidad, formular observaciones y habilitar la presentación. **No modifica datos provinciales.** |
| **8. Subsanación.** La provincia responde las observaciones editando en el sistema y vuelve a cerrar la carga. | Operador provincial edita · Responsable provincial cierra | Resolver cada observación dejando constancia. |
| **9. Presentación y consolidación.** El responsable provincial presenta formalmente el período y descarga el comprobante para remitir por GDE. Los datos de la Capa 2 se incorporan a la base consolidada de la Capa 3. | Responsable provincial presenta · SISOC consolida | Formalizar la presentación del período. |

<!-- COMENTARIO: los pasos 1 y 2 pueden variar según cómo se resuelva el
     universo de personas (ver 08-analisis-de-las-planillas.md, apartado 1). Si
     se adopta un archivo de universo, el orden pasa a tres momentos:
     dispositivos, universo y medidas. No altera la lógica del circuito ni la
     distribución de responsabilidades. -->

---

## Estados de la presentación

El circuito se refleja en el estado de la presentación. Son ocho, y no se mezclan
con el estado de cada importación: una presentación puede tener importaciones
anuladas y estar igual en condiciones de cerrarse.

```
EN_CARGA ──cerrar carga──▶ CERRADA ──abrir revisión──▶ EN_REVISION
    ▲                                                        │
    │                                        ┌───────────────┴───────────────┐
    │                                        │                               │
reabrir / cerrar carga                   observar                sin observaciones
    │                                        │                               │
SUBSANADA ◀──responder──── OBSERVADA ◀───────┘                        HABILITADA
                                                                              │
                                                                         presentar
                                                                              │
                                                      CONSOLIDADA ◀───── PRESENTADA
```

| Estado | Significa |
|---|---|
| En carga | La jurisdicción está cargando y corrigiendo |
| Carga cerrada | Enviada a revisión nacional |
| En revisión | El revisor técnico nacional la está revisando |
| Observada | Tiene observaciones y volvió a la jurisdicción |
| Subsanada | Se respondieron las observaciones; falta cerrar la carga |
| Habilitada | La revisión concluyó sin observaciones pendientes |
| Presentada | Presentación formal realizada; comprobante disponible |
| Consolidada | Los datos se incorporaron a la base consolidada |

---

## Reglas que sostienen el circuito

Están implementadas y verificadas. No son recomendaciones.

1. **Un error bloqueante impide la importación completa del archivo.** No se
   incorporan las filas válidas por separado. Garantiza que la información de un
   período corresponda a un mismo momento y no a cargas parciales sucesivas.
2. **Una advertencia no impide la importación** y se resuelve dentro del sistema.
3. **Una vez importado el archivo, las correcciones se hacen dentro del sistema.**
   No se vuelve a subir el Excel salvo que el problema sea el archivo completo
   —por ejemplo, casos omitidos—, en cuyo caso la nueva importación anula la
   anterior y descarta las ediciones realizadas sobre ella.
4. **Para reimportar después del cierre hay que reabrirlo**, de modo que el
   revisor nacional no trabaje sobre datos que cambiaron abajo.
5. **El cierre de carga es responsabilidad del responsable provincial**, no del
   operador. Es la declaración de que el período está en condiciones de revisarse.
6. **El nivel nacional no modifica datos provinciales.** Sólo formula
   observaciones. Toda corrección la realiza la jurisdicción.
7. **El ciclo de observación y subsanación no tiene límite de rondas.**
8. **La presentación es el último acto del circuito** y ocurre una vez que el
   revisor técnico nacional habilitó esa opción.
9. **Una vez consolidada, la información del período no se modifica.** Los errores
   detectados con posterioridad se informan en el período siguiente.

---

## Comprobante de presentación

Al confirmar la presentación, el sistema genera un comprobante exportable con la
jurisdicción, el período, los archivos comprendidos, la versión presentada y la
fecha del acto.

Su finalidad es dejar **constancia formal de que la jurisdicción cumplió con la
entrega** en tiempo y forma. Constituye un resguardo para la provincia.

El responsable provincial lo descarga, lo remite por GDE e incorpora al sistema
el número de expediente obtenido. Dado que se trata de un resguardo documental y
no de una instancia de validación, **la ausencia del número no impide la
consolidación**: la información ya fue revisada y aceptada. El sistema señala las
presentaciones que aún no tienen número incorporado.

---

## Continuidad de las medidas entre períodos

Una persona informada en un período puede no aparecer en el siguiente. En
principio es esperable: la medida concluyó.

La situación a atender es otra: **una medida informada como vigente —sin fecha de
finalización— que deja de aparecer en el período siguiente.** El sistema no
tendría con qué darla por concluida, y quedaría registrada como vigente de manera
indefinida.

Se propone que la ausencia no se interprete automáticamente como finalización. Al
comparar con el período anterior, SISOC identifica esas medidas y las presenta a
la jurisdicción para que confirme si concluyó —informando la fecha— o si su
omisión fue un error de carga.

<!-- COMENTARIO: esto depende de que MPI y MPE incorporen fecha de finalización.
     Hoy no la tienen (ver 08-analisis-de-las-planillas.md, apartado 5), así que
     el sistema puede detectar el caso pero no cerrarlo. -->

---

## Definiciones pendientes

> **Anulación excepcional.** Se propone que un error detectado después de la
> consolidación se corrija en el período siguiente, conservando el histórico tal
> como fue presentado. Corresponde definir si además debe existir una anulación
> excepcional a cargo del nivel nacional, que revierta la consolidación. La
> decisión afecta la continuidad de la serie estadística.

> **Alcance del rol de responsable provincial.** Se propone que pueda realizar
> también las tareas del operador, ya que en jurisdicciones chicas puede tratarse
> de la misma persona. Corresponde confirmar si ambos roles deben mantenerse
> estrictamente separados.

<!-- COMENTARIO: en el prototipo el responsable NO puede importar; sólo cierra y
     presenta. Si se confirma que debe poder, se amplía `puede_cargar` en
     permissions.py. -->
