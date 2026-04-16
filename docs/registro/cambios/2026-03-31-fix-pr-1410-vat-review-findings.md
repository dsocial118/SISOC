# VAT: corrección de hallazgos bloqueantes del PR 1410

Fecha: 2026-03-31

## Cambio

Se corrigieron tres puntos de alto riesgo detectados en la revisión del PR 1410:

- compatibilidad `PlanVersionCurricular -> titulo_referencia` ajustada al `related_name` nuevo (`titulos`);
- serializers VAT alineados al esquema nuevo, evitando referencias a campos eliminados (`sector`, `subsector`, `version`, `frecuencia`);
- migración `0021` endurecida para fallar explícitamente si encuentra títulos históricos asociados a más de un plan.

## Decisión clave

Ante ambigüedad histórica en la inversión `Título -> Plan de Estudio`, la migración ya no elige un plan arbitrario.

Si existe más de un plan previo para un mismo título, la migración aborta con un error claro para forzar resolución manual antes del deploy.

## Validación esperada

- Los serializers de títulos y planes vuelven a serializar sin `AttributeError`.
- La compatibilidad usada por templates, `__str__` y serializers vuelve a funcionar.
- El deploy no degrada datos silenciosamente si la base productiva contiene relaciones históricas no invertibles de forma unívoca.
