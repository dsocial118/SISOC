# Instrumento DataCalle

Copia de los artefactos que publica la app en
`Desktop/DataCalle-SISOC/contrato/`. **No editar a mano**: los regenera
DATACALLE y se sincronizan pidiéndolo en el canal de coordinación.

SISOC los usa para dos cosas, ninguna de las cuales condiciona el contrato:

- mostrar las respuestas de un caso con etiquetas legibles en el backoffice;
- servir `GET /api/datacalle/catalogos/`, para que la app pueda actualizar
  textos y opciones sin publicar una versión nueva.

Las respuestas se guardan siempre como llegan, así que una versión desfasada
del cuestionario nunca pierde datos: sólo muestra la clave cruda.
