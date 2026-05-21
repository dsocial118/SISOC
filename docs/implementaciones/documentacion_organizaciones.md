# Documentacion organizacional

## Objetivo

Centralizar documentacion de organizaciones para que admisiones, comedores y relevamientos reutilicen una fuente documental versionada sin duplicar archivos por flujo.

## Modelo funcional

- `DocumentacionOrganizacion`: catalogo de documentacion requerida por categoria de organizacion.
- `ArchivoOrganizacion`: archivo cargado para una organizacion y una documentacion requerida.
- Estados de archivo: `Pendiente`, `Documento adjunto`, `A Validar Abogado`, `Rectificar`, `Aceptado`.
- Cada archivo puede tener vencimiento, observaciones, numero GDE y usuario de modificacion.
- Los archivos aceptados se conservan como historial; los no aceptados pueden ser reemplazados por una nueva carga.

## Reglas de uso

- La documentacion disponible depende del tipo/subtipo de organizacion.
- La dupla asignada al comedor vinculado limita quien puede cargar o validar documentacion.
- Tecnico y abogado tienen acciones diferenciadas sobre carga, validacion y rectificacion.
- Al finalizar informe tecnico de admision, la documentacion organizacional se congela copiandose al flujo de admision.
- `numero_gde` se conserva tanto en organizacion como en las copias documentales usadas por admisiones.

## Superficies

- Detalle de organizacion: carga, estado, GDE, vencimiento y acciones por documento.
- Historial de documentacion: pagina separada por organizacion/documentacion.
- Admisiones: reutiliza documentacion organizacional cuando no existe documento propio y congela la evidencia al cerrar informe tecnico.
- Relevamientos: agrega `numero_if` como dato editable desde el listado del comedor y lo excluye del serializer hacia Gestionar.

## Pendientes conocidos

- En una iteracion posterior conviene enlazar admisiones contra una version exacta de `ArchivoOrganizacion` en lugar de depender solo de copia congelada.
- Si cambian nombres productivos de categorias documentales, revisar la clasificacion por tipo/subtipo antes de desplegar.
