# 2026-09-10 - PAS: impacto RENAPER, género y domicilio

## Cambio funcional

- Al preparar una corrida mensual RENAPER se aplican las incompatibilidades de
  supervivencia vencidas: el titular pasa a `Baja`, queda con el aviso
  `40 (FALLECIDO)`, se registra el historial y la novedad pasa a gestionada.
- Una detección repetida y una persona que ya está en `Baja/FALLECIDO` no crean
  otra novedad pendiente ni aparecen entre los próximos cambios de estado.
- La importación del padrón admite `Genero`, `ciudadano_genero` y
  `ciudadano_genero_cod` con valores `M`, `F` o `X`.
- El alta y la edición del padrón desde el backoffice incluyen el género, que
  es el único camino para completarlo en titulares ya existentes: la
  importación sólo crea y omite los DNI/CUIT ya cargados.
- Editar el domicilio desde el backoffice vuelve a derivar calle y altura, que
  son los campos que la DDJJ pública muestra con prioridad.
- RENAPER usa directamente `M` o `F` cuando el padrón lo informa. Para género
  vacío o `X` mantiene el fallback `M` y luego `F` ante `no_match`.
- Calle y Altura se persisten por separado en PAS, sin dejar de mantener el
  domicilio compuesto. La DDJJ pública presenta ambos campos por separado y
  conserva compatibilidad con registros históricos que sólo poseen domicilio.
- En mobile, la DDJJ mantiene fijos los banners superior e inferior y limita el
  desplazamiento al contenido central, usando el alto dinámico del dispositivo.
- La DDJJ adopta el flujo UX de cinco pasos y sus textos visibles. Las preguntas
  de controles de embarazo y de vacunación/escolaridad se muestran en el mismo
  paso al responder afirmativamente y se deshabilitan al volver a responder No.
- El último paso muestra todas las respuestas aplicables y deja de solicitar la
  firma con nombre completo. Ese dato también se excluye de las nuevas DDJJ y de
  la visualización del historial en el panel de control.
- Las opciones Sí/No se presentan como botones de texto sin el control de radio
  visible. La selección usa fondo gris `#CBCDD4` y un foco amarillo atenuado;
  las acciones de retroceso muestran el texto `Atrás`. Como el estado marcado y
  el foco dependen de `:has()`, un bloque `@supports not (selector(:has(*)))`
  restituye el radio nativo en los navegadores que no lo soportan (Chrome <105,
  Firefox <121, WebViews Android antiguas), para que el titular siempre vea qué
  opción eligió.
- El encabezado público usa la marca gráfica de Formando Capital Humano sin
  círculo, con `FORMANDO` en peso regular y `CAPITAL HUMANO` en negrita.
- En el primer paso, la acción principal se presenta como `Confirmar y
  continuar`; en los pasos intermedios conserva el texto `Continuar`.

## Datos y despliegue

La migración `pas.0007_paspersona_genero_calle_altura` agrega tres columnas
opcionales, por lo que los registros existentes siguen siendo válidos. No se
modifican permisos ni se agregan dependencias.

La migración `pas.0008_remove_ddjj_firma_respuestas` borra la clave
`firma_nombre_completo` del JSON `respuestas` de todas las DDJJ históricas y
**no tiene reverso** (`RunPython.noop`). El dato no se pierde: el PDF firmado de
cada declaración es inmutable y sigue siendo la fuente de verdad legal; lo que
se elimina es la copia editable en la base. El panel de control además filtra la
clave en el template, así que una migración parcial no rompe la vista.

### Verificación previa al despliegue

`aplicar_bajas_fallecimiento_pendientes` corre al preparar cada ciclo mensual y
aplica **todas** las incompatibilidades de supervivencia pendientes cuyo período
de impacto ya venció. La primera corrida posterior a este cambio procesa el
backlog acumulado de una sola vez, y la baja no se revierte automáticamente. Hay
que medir el volumen antes de desplegar:

```python
from pas.models import PasIncompatibilidad

PasIncompatibilidad.objects.filter(
    categoria="supervivencia", estado="pendiente"
).values("persona").distinct().count()
```

Ese número es la cantidad de titulares que van a pasar a `Baja` en el primer
ciclo. Si resulta mayor de lo esperado, conviene acordar con el área un tope por
ciclo antes de habilitar el job. Cada corrida deja el registro
`pas.renaper.bajas_aplicadas` con `periodo`, `pendientes`, `personas`,
`actualizadas` y `ya_aplicadas`, y cada cambio queda en `PasHistorialEstado` con
el estado y los avisos anteriores, que es la vía para revertir una baja mal
aplicada.

## Pendiente

- Confirmar contra un export real de GESTIONAR qué contiene la columna
  `ciudadano_genero_cod`: hoy se valida contra los literales `M`, `F` y `X`, y
  si el origen informa códigos numéricos la importación va a rechazar cada fila
  con un error explícito.
- Definir cómo se completa el género del padrón ya cargado. La importación sólo
  crea registros nuevos, así que hoy el único camino es la edición desde el
  backoffice. Mientras tanto esos titulares conservan el fallback `M` y luego
  `F`, que funciona pero duplica las consultas a RENAPER.
