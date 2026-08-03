# UI unificada para el Gestor de templates

## Editor enriquecido de contenido

El contenido de las versiones borrador se puede redactar visualmente, sin
necesidad de escribir HTML para las operaciones habituales. La barra permite
deshacer/rehacer, estilos de párrafo, negrita, cursiva, subrayado, color,
listas, alineación —incluida la justificada—, tablas, enlaces, separadores,
pantalla completa y la vista de HTML avanzada.

Las variables documentales se insertan como etiquetas visuales no editables,
pero se serializan nuevamente como `{{ variable }}` al guardar. De ese modo la
generación de DOCX y la validación del catálogo continúan usando el contrato
existente.

El contenido pegado se incorpora como texto sin formato y el formulario admite
sólo el subconjunto de HTML necesario para DOCX. Se excluyen scripts, iframes,
imágenes y atributos activos; esto evita que un borrador pueda ejecutar o
cargar contenido externo al volver a editarse.

El lienzo de edición representa una hoja A4 vertical, centrada, con márgenes
de 20 mm y tipografía base Times New Roman de 12 pt. El mismo formato se aplica
al DOCX de los templates dinámicos para que la composición sea predecible antes
de descargarlo.

La barra del editor muestra una descripción en español al pasar el mouse por
cada herramienta. Sus menús de estilos, colores, alineación y tablas se
gestionan de forma compatible con Bootstrap 5, por lo que no dependen del
comportamiento de dropdowns de Bootstrap 4 incluido por Summernote.

## Cambio visible

Las pantallas de Templates, Variables documentales e Incidencias de templates
se presentan como secciones de un único **Gestor de templates**. Comparten una
cabecera de contexto, navegación interna, tarjetas, filtros, tablas y estados
vacíos consistentes con los patrones existentes de SISOC.

El editor de versiones mantiene la inserción por clic y arrastre de variables,
pero en pantallas chicas prioriza el área de edición antes que el catálogo.

El detalle de un template prioriza la gestión de versiones: sus condiciones se
presentan como una única franja de contexto y la tabla de versiones ocupa todo
el ancho disponible. Las acciones de cada versión mantienen su jerarquía
visual: editar/publicar primero y restaurar como acción secundaria.

El editor de una versión usa todo el ancho disponible. El catálogo de variables
queda inicialmente colapsado y se puede expandir sin salir de la pantalla; al
abrirlo mantiene sus operaciones de búsqueda, clic y arrastre.

El editor se organiza en cuatro paneles colapsables: variables disponibles,
contenido del template, observaciones de la versión y vista previa. El
contenido queda abierto por defecto; las secciones auxiliares se abren sólo
cuando son necesarias. El catálogo identifica cada categoría y mantiene sus
tarjetas visualmente equilibradas.

Se unificó el radio de las cabeceras de las tarjetas en todo el Gestor,
incluidos los formularios, para que el color llegue hasta las esquinas del
contenedor sin el radio propio de Bootstrap.

En el menú lateral, Variables documentales e Incidencias de templates pasan a
ser opciones hijas de Gestor de templates. Las rutas y permisos se conservan.

## Alcance técnico

- Estilos aislados en `static/custom/css/gestor_templates.css`.
- Navegación compartida en
  `admisiones/templates/admisiones/templates_informes_tecnicos/includes/navigation.html`.
- Reutilización del componente global `components/empty_state.html` y de los
  patrones Bootstrap/AdminLTE ya utilizados por SISOC.

No se modifica la lógica de selección, publicación, incidencias ni generación
de DOCX.
