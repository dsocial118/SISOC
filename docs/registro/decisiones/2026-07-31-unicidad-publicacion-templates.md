# Unicidad de publicación de templates en MySQL

Fecha: 2026-07-31

## Decisión

Usar una tabla interna de publicaciones vigentes por combinación de
condiciones, con una clave única persistida, en lugar de una restricción única
condicional sobre las versiones.

## Motivo

MySQL no implementa restricciones únicas condicionales. La regla funcional
requiere impedir que dos plantillas distintas queden publicadas para la misma
combinación, incluso si dos administradores publican casi al mismo tiempo.

## Consecuencia

La publicación se realiza transaccionalmente. El registro único referencia la
versión vigente y será también la fuente de selección automática en la etapa
de generación de DOCX.
