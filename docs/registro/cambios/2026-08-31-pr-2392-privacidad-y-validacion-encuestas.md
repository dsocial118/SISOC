# Encuestas: privacidad y validación de respuestas

Se corrige el modelo de anonimato: la identidad usada para evitar respuestas
duplicadas se almacena separada del contenido anónimo. También se validan los
valores recibidos fuera de la UI, se neutralizan fórmulas en exportaciones y se
reducen consultas de pendientes y resultados.

La segmentación de todos los usuarios incluye ahora al creador; las rutas de
gestión permanecen accesibles a quien posee el permiso de cambio para evitar un
bloqueo operativo por una encuesta obligatoria propia.
