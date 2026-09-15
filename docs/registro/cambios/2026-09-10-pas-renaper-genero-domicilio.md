# 2026-09-10 - PAS: impacto RENAPER, género y domicilio

## Cambio funcional

- Al preparar una corrida mensual RENAPER se aplican las incompatibilidades de
  supervivencia vencidas: el titular pasa a `Baja`, queda con el aviso
  `40 (FALLECIDO)`, se registra el historial y la novedad pasa a gestionada.
- Una detección repetida y una persona que ya está en `Baja/FALLECIDO` no crean
  otra novedad pendiente ni aparecen entre los próximos cambios de estado.
- La importación del padrón admite `Genero`, `ciudadano_genero` y
  `ciudadano_genero_cod` con valores `M`, `F` o `X`.
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
  las acciones de retroceso muestran el texto `Atrás`.
- El encabezado público usa la marca gráfica de Formando Capital Humano sin
  círculo, con `FORMANDO` en peso regular y `CAPITAL HUMANO` en negrita.
- En el primer paso, la acción principal se presenta como `Confirmar y
  continuar`; en los pasos intermedios conserva el texto `Continuar`.

## Datos y despliegue

La migración `pas.0007_paspersona_genero_calle_altura` agrega tres columnas
opcionales, por lo que los registros existentes siguen siendo válidos. No se
modifican permisos ni se agregan dependencias.
