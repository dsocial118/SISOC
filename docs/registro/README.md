# Spec-as-Source en SISOC

Este directorio define la convencion para documentacion operativa y de cambios.

## Reglas obligatorias

1. Antes de implementar, leer `AGENTS.md`, `docs/indice.md` y solo el contexto minimo necesario para la tarea.
2. Registrar en `docs/` cada cambio o decision importante.
3. No depender de herramientas externas de spec-driven development; la fuente de verdad vive en Markdown dentro del repo.

## Carga minima recomendada

Inicio:
- `AGENTS.md`
- `docs/indice.md`
- archivo objetivo
- tests del modulo
- una guia relevante de `docs/ia/`

Ampliar solo si el cambio toca reglas funcionales, permisos, seguridad o comportamiento observable.

## Convencion sugerida

- `docs/registro/cambios/`
- `docs/registro/decisiones/`
- `YYYY-MM-DD-<tema>.md`

## Artefactos obligatorios de pull request

Cada PR debe conservar en su rama origen:

- `docs/registro/prs/PR-<numero>.md`;
- `docs/contexto/features/pr-<numero>-<slug>.md`.

Cuando el destino es `main`, también debe incluir una nota en
`docs/registro/releases/pending/` y el bloque correspondiente en
`CHANGELOG.md`.

Para ramas internas no protegidas, `.github/workflows/pr-docs.yml` genera y
pushea estos archivos. Las ramas protegidas (`development`, `homologacion` y
`main`) no se autoescriben: si faltan artefactos, el workflow los informa en
su Summary sin bloquear la promoción.

Cuando se requiera conservar los artefactos de una promoción o el bot no pueda
escribir la rama, generarlos de forma explícita antes de abrir o actualizar el
PR:

```powershell
$env:GITHUB_TOKEN = gh auth token
python scripts/ci/pr_doc_automation.py --repository dsocial118/SISOC --pr <numero>
```

Revisar y commitear únicamente los paths generados. Para una promoción a
`main`, confirmar además que la release note y el bloque de `CHANGELOG.md`
describen la fecha objetivo correcta.

## Cuando registrar

- cambios funcionales visibles,
- decisiones de arquitectura o diseno,
- cambios de seguridad, permisos o datos sensibles,
- trade-offs relevantes para mantenimiento.

## Cuando puede no aplicar

Si el cambio es trivial y sin impacto funcional, se puede omitir el archivo, pero debe quedar justificado en la entrega.
