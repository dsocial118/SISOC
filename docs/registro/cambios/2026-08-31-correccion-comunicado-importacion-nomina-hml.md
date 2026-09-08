# Corrección del comunicado de importación de nómina en HML

## Evidencia

La verificación autenticada posterior al despliegue mostró que el comunicado
interno `📋 Importación de nómina en nuevas admisiones` seguía publicado.

La migración correctiva anterior usaba `titulo__istartswith` y no alcanzaba el
registro real porque su título comienza con un emoji.

## Corrección

La nueva migración vuelve a buscar comunicados internos publicados que
contengan la frase estable `Importación de nómina`, los archiva y quita su marca
de destacado. La reversa es deliberadamente vacía porque no es seguro volver a
publicar contenido automáticamente.

Se agregó una regresión con el título exacto observado en HML.
