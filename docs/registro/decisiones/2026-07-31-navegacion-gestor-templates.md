# Decisión: Variables e incidencias son secciones del Gestor de templates

## Contexto

Variables documentales e Incidencias de templates existen para administrar el
contenido y las combinaciones del mismo circuito de templates. Mostrarlas como
opciones independientes de Configuración de Comedores fragmentaba ese flujo.

## Decisión

Se agrupan en una navegación interna y en un submenú lateral bajo **Gestor de
templates**:

- Templates
- Variables documentales
- Incidencias de templates

## Consecuencias

- Se conserva cada URL, vista y permiso actual; sólo cambia su presentación y
  jerarquía de navegación.
- El estilo queda aislado al módulo para no acoplar Comedores con las hojas de
  estilo particulares de Centros de Familia o INET.
