# 2026-08-25 - Reconciliación de migraciones PWA en `pwanueva`

## Contexto

La rama PWA histórica aplicó `comedores` 0048-0050 para incorporar
`ImagenComedor.client_uuid`, su restricción única y `relevamiento`. Al integrar
la rama con la numeración vigente, esas operaciones quedaron reunidas en la
migración 0056, que podía volver a ejecutar DDL sobre entornos ya actualizados.

## Decisión

- `comedores.0056` conserva el estado final de Django y omite la creación de
  cada columna o restricción si ya existe con el nombre esperado.
- `users.0048_merge_pwa_territorial_and_organizacion` une la hoja territorial
  de PWA con la cadena de accesos por organización que llega desde Homologación.

## Operación

La migración es segura para una base limpia y para una base que ya aplicó la
cadena PWA anterior. Su reversión no elimina columnas ni restricciones, para no
arriesgar datos cuyo origen histórico no puede determinarse de forma segura.
