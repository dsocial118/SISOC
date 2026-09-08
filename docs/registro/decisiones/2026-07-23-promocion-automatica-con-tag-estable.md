# 2026-07-23 - Promoción automática con baseline estable

## Estado

- Aceptada.

## Contexto

El pre-deploy semanal debe iniciar a las 16:30, cuando todavía pueden entrar
cambios en `development`, pero no debe mantener una sesión de Codex esperando
CI. La promoción a producción conserva una aprobación humana en el Environment
`production` de GitHub Actions.

## Decisión

- La tarea programada prepara o reutiliza un PR exacto `development -> main` en
  draft y, si hace falta, un PR temporal de saneamiento hacia `development`.
- Los PRs se arman para el auto-merge nativo de GitHub; los workflows no hacen
  `pulls.merge` con `GITHUB_TOKEN`, porque esos merges no disparan los flujos
  posteriores de CI/deploy. El orquestador recibe eventos de PR y CI, deja
  listo el PR final y habilita su auto-merge una vez armada la baseline.
- El PR final declara el SHA de `development` que fue analizado. Si entra otro
  commit después del snapshot, el workflow bloquea la promoción hasta que una
  nueva ejecución actualice análisis, changelog y marcador.
- Justo antes de integrar a `main`, se crea un tag anotado e inmutable con el
  formato `AAAA.MM.DD-stable`, apuntando al `main` que se va a reemplazar. Si
  ya existe con otro SHA, la promoción se bloquea en vez de sobrescribir un
  baseline de rollback.
- El check requerido `release_baseline` permanece pendiente hasta que el tag y
  la release del baseline existen. Solo entonces se completa en verde y GitHub
  puede hacer el merge nativo.
- Los deploys usan el SHA del evento. Si la rama avanzó antes de aprobar o
  ejecutar el job, se omiten antes del downtime; nunca hacen deploy de un SHA
  más nuevo bajo una aprobación anterior.

## Consecuencias

- Codex termina luego de armar el estado verificable; GitHub espera CI y hace
  los merges, por lo que no hay una sesión larga ni un merge manual rutinario.
- `main` nuevo debe sincronizarse hacia `development` y volver a pasar gates
  antes de una promoción; no se puede publicar una base obsoleta.
- La fecha del tag permite un baseline por día. Una segunda promoción el mismo
  día con otro `main` requiere una decisión explícita, para no perder rollback.
- Las rulesets deben exigir los checks definidos en los workflows y permitir
  auto-merge sin aprobación manual. Configurarlas requiere permisos de
  administrador del repositorio.
- Los workflows usan una GitHub App privada, no un PAT, para las mutaciones que
  deben disparar otros workflows. Cada job genera un installation token efímero
  limitado al repositorio actual con `Contents`, `Pull requests`, `Checks` e
  `Issues` en escritura, más `Metadata` en lectura. La App se configura con la
  variable `RELEASE_AUTOMATION_APP_CLIENT_ID` y el secret
  `RELEASE_AUTOMATION_APP_PRIVATE_KEY`; ambos requieren configuración de
  administrador. La ruleset de `main` fija `release_baseline` a esa misma App
  como fuente, para no aceptar checks homónimos de otra integración.

## Referencias

- `.github/workflows/release-orchestrator.yml`
- `.github/workflows/sync-main-downstream.yml`
- `.github/workflows/deploy.yml`
- `scripts/operacion/deploy_refresh.sh`
- `docs/operacion/deploy_automatizado.md`
