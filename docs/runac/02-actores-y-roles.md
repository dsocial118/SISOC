# Actores y roles

Dos cosas distintas que conviene no mezclar: los **actores del proyecto**, que
deciden mientras se construye, y los **roles del sistema**, que lo usan una vez
hecho.

---

## Actores del proyecto

| Actor | Quién es | Qué decide |
|---|---|---|
| **Contraparte** | Dirección Nacional de Promoción y Protección Integral (DNPYPI), área requirente | Reglas de negocio, qué datos se piden, qué es error y qué advertencia, circuito, reportes, periodicidad |
| **Coordinación** | Área del CNCPS a cargo del proyecto | Qué información existente de SISOC se habilita para RUNAC: RENAPER, seguridad social, datos sensibles. Prioridades y alcance por etapa |
| **Equipo de desarrollo** | Equipo SISOC | Cómo se implementa: modelo de datos, integración al monolito, patrones, performance |
| **Responsable funcional** | Analista del proyecto | Traduce entre los tres. Propone y sostiene el análisis |

---

## Roles del sistema

Son cuatro. El **rol** define qué puede hacer; la **jurisdicción**, sobre qué
datos. Son dos ejes distintos: un mismo rol existe en las 24 jurisdicciones.

| Rol | Qué puede hacer |
|---|---|
| **Operador provincial** | Importar archivos, consultar errores, **corregir datos dentro del sistema** y responder observaciones |
| **Responsable provincial** | Revisar lo cargado, **cerrar la carga**, responder observaciones y **presentar el período**. Responde institucionalmente por los datos |
| **Revisor técnico nacional** | Revisar calidad, **formular observaciones** y **habilitar la presentación**. No modifica datos provinciales |
| **Administrador nacional** | Gestionar usuarios, jurisdicciones, períodos, catálogos y la estructura de los archivos |

### Qué ve cada rol

El menú no es una comodidad: es parte del permiso. Cada rol ve sólo sus
secciones, y **el acceso se verifica también al entrar por dirección directa** —
ocultar un enlace no impide escribir la URL.

| Sección | Operador | Responsable | Revisor | Administrador |
|---|---|---|---|---|
| Inicio | ✓ | ✓ | ✓ | ✓ |
| Plantillas | ✓ | ✓ | — | ✓ |
| Cargar archivos | ✓ | ✓ | — | — |
| Resultado del período | ✓ | ✓ | ○ | — |
| Revisión nacional | — | — | ✓ | ✓ |
| Estructura de los archivos | ✓ | ✓ | ✓ | ✓ |

✓ en el menú · ○ accesible, pero no en el menú: el revisor llega desde la bandeja
de revisión con el enlace «Ver carga».

---

## Quién hace qué en el circuito

| Acción | Quién |
|---|---|
| Importar un archivo | Operador provincial |
| Corregir un dato ya importado | Operador provincial |
| Cerrar la carga | Responsable provincial |
| Reabrir la carga | Responsable provincial |
| Formular una observación | Revisor técnico nacional |
| Responder una observación | Operador provincial |
| Habilitar la presentación | Revisor técnico nacional |
| Presentar el período | Responsable provincial |
| Registrar el número de expediente | Responsable provincial |
| Definir la estructura de un período | Administrador nacional |

**Dos reglas que atraviesan todo:**

- El **nivel nacional no modifica datos provinciales**. Observa. Toda corrección
  la hace la jurisdicción.
- Quien **carga** no es quien **cierra**: el operador prepara, el responsable
  declara que está listo. Es lo que hace que el cierre sea un acto y no un
  trámite.

---

## Acceso a datos nominales

Debe ser restringido y registrado. Las descargas para análisis nacional salen
**pseudonimizadas por defecto**: sin nombre, apellido, documento ni CUIL,
conservando el identificador interno y las variables necesarias.

<!-- COMENTARIO: en el prototipo esto no está implementado. Los roles y el
     alcance territorial se resuelven con permissions.py, que es provisorio: al
     integrar el módulo, SISOC lo resuelve con iam/services.py y su propio
     alcance territorial. La auditoría de accesos tampoco está: la aporta
     audittrail. -->
