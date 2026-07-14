# Plan A: sincronizacion descendente desde `main`

Estado: aprobado para implementacion el 2026-07-14.

## Objetivo

Mantener este invariante sin supervision cotidiana:

- `main` contiene solamente lo que se publica en produccion;
- `development` contiene todo `main` y puede sumar cambios de QA;
- `homologacion` contiene todo `main` y puede sumar cambios de HML;
- integrar `main` en una rama inferior nunca copia los extras de esa rama hacia
  `main`.

La promocion funcional sigue siendo `development -> homologacion -> main`. La
sincronizacion de este plan opera en sentido inverso solo para evitar que QA o
HML pierdan correcciones ya productivas.

## Diseno

Un workflow separado se ejecuta al recibir un push en `main`, por invocacion
manual y periodicamente como reconciliacion. Para cada rama objetivo:

1. comprueba si `main` ya es ancestro de la rama;
2. si falta contenido, abre o reutiliza un PR `main -> rama objetivo`;
3. espera que GitHub calcule si el PR puede integrarse;
4. lo integra con merge commit solamente cuando no hay conflictos;
5. invoca de forma explicita el workflow de deploy sobre la rama actualizada.

El dispatch explicito es obligatorio: un push producido con `GITHUB_TOKEN` no
inicia otro workflow basado en `push`. No se agrega PAT ni otra credencial.

## Seguridad y fallos

- Nunca se fuerza un push, rebase, reset ni resolucion automatica de conflictos.
- Un conflicto deja el PR abierto y el job en error; ese entorno no se despliega.
- Si GitHub rechaza el merge, el workflow conserva el PR y falla con diagnostico.
- Si la rama ya contiene `main`, no crea commits ni despliega de nuevo.
- La concurrencia es serial para toda la reconciliacion y no cancela
  ejecuciones en curso.
- `main` nunca es base ni destino de una escritura de este workflow.
- Produccion conserva su Environment protegido y no se aprueba desde este flujo.

## Deploy asociado

`deploy.yml` acepta tanto `push` como `workflow_dispatch`. Los jobs siguen
seleccionandose por `github.ref`, por lo que un dispatch con ref `development` o
`homologacion` ejecuta solamente QA o HML. Un dispatch a `main` sigue sujeto al
Environment `production` y no forma parte de la sincronizacion automatica.

## SISOC-Mobile

El repositorio mobile es publico. El deploy valida que el checkout corresponda
a `dsocial118/SISOC-Mobile` y normaliza solamente las variantes conocidas del
remote `origin` a HTTPS publica antes del fetch. Un remote desconocido bloquea
el deploy. Esto evita depender de una clave SSH en QA, HML o PRD sin aceptar un
repositorio arbitrario.

## Rollback

1. deshabilitar manualmente el workflow de sincronizacion;
2. revertir el commit que lo incorpora;
3. no revertir automaticamente merges ya aplicados en ramas inferiores;
4. si un merge descendente causara una regresion, revertir ese merge mediante
   un PR normal sobre la rama afectada y ejecutar su health check.

No hay cambios de base de datos, secretos, permisos de servidor ni servicios en
esta implementacion.
