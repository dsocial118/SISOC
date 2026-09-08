# Issue 2443: descarga de Informe Técnico para GDE

## Objetivo

Corregir el formato de la descarga DOCX para GDE y ubicarla en el flujo técnico
posterior a la validación legal, sin alterar el circuito de edición, revisión o
carga manual del IF.

## Decisión

- El DOCX inicial y el DOCX editado siguen su flujo actual.
- La descarga se muestra como acción técnica cuando `InformeTecnico.estado` es
  `Validado`; no registra una descarga ni modifica estados.
- El endpoint exige técnico de la dupla activa y el mismo estado validado. Se
  mantiene la excepción administrativa actual para superusuarios.
- El archivo GDE es una copia transitoria y no se vincula a
  `archivo_informe_tecnico_GDE` ni a `numero_if_tecnico`.
- El estilo `Normal` del DOCX exportado se justifica para que el contenido sin
  alineación explícita no quede a la izquierda. Las alineaciones explícitas de
  títulos y celdas se preservan.

## Alcance técnico

1. Quitar el enlace de la vista de revisión del informe.
2. Agregar la acción de descarga a los botones técnicos.
3. Validar rol técnico de dupla y estado en la vista de descarga.
4. Corregir el estilo base del DOCX GDE.
5. Cubrir formato, permisos y disponibilidad de acciones con tests focalizados.

## Criterios de aceptación

- Un abogado no ve ni puede descargar el DOCX GDE.
- Un técnico autorizado puede descargarlo una vez validado el informe.
- La carga manual de IF queda disponible sin descargar antes y no cambia por
  descargar.
- Los párrafos sin alineación explícita del DOCX GDE quedan justificados, sin
  modificar párrafos centrados explícitamente.
