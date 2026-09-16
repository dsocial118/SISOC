# Estabilización de CI del PR 2438

## Causa confirmada

El commit funcional de PAS dejó finales de línea mezclados y un import de
servicios antes de los imports de Django. Black y Pylint bloquearon el deploy
guard. En la misma ejecución, los workflows de autofix y documentación
intentaron escribir la rama en paralelo; el segundo `git push` perdió la
carrera aunque los artefactos se habían generado correctamente.

Los dos tests de reutilización del token RENAPER pasaban de forma aislada y con
`xdist`, pero usaban respuestas construidas con `Mock` sin un contrato HTTP
explícito. Eso dificultaba distinguir una regresión del cliente de una
diferencia del entorno de CI.

## Corrección

- Se normalizaron los archivos PAS afectados y se reordenaron los imports.
- Los tests RENAPER usan una respuesta determinista que implementa
  `raise_for_status()` y `json()`, y comprueban también la cantidad de consultas.
- La documentación automática serializa sus ejecuciones por PR. Si otra
  automatización hace avanzar la rama, actualiza su base mediante `fetch` y
  `rebase`, y reintenta el push hasta tres veces. Un conflicto real sigue
  bloqueando el job para evitar sobrescribir cambios.

## Validación

- Black sobre los archivos Python afectados.
- Pylint sobre modelos, views y tests afectados: 10/10.
- `pas/tests/test_supervivencia_jobs.py` con `pytest -n auto`.
- Contrato unitario del workflow de documentación automática.
