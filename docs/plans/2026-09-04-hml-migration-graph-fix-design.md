# Corrección del grafo de migraciones para HML

## Problema

`users.0049_coordinadorequipotecnico_pwa` depende de
`comedores.0050_imagencomedor_relevamiento`, pero esa migración no existe en
las ramas operativas `development` y `homologacion`. Django no puede cargar el
grafo y el arranque de HML se detiene antes de ejecutar migraciones.

## Decisión

Actualizar esa dependencia a la hoja vigente de `comedores` que contiene la
evolución de `ImagenComedor` y `relevamiento`:
`0056_imagencomedor_client_uuid_imagencomedor_relevamiento_and_more`.

No se crea una migración nueva ni se reintroduce `0050`: el grafo actual es
inválido, por lo que `users.0049` no pudo haberse aplicado mediante Django.

## Validación

La CI debe cargar el grafo mediante `migrations_check`, ejecutar las pruebas
requeridas y permitir el auto-merge. Luego se promueve el mismo corte desde
`development` a `homologacion` para disparar el deploy HML.
