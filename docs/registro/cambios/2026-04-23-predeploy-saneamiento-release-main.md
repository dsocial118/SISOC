# 2026-04-23 - Saneamiento final para release `development -> main`

## Contexto

- Se retomó el pre-deploy abierto el `2026-04-23` entre `origin/development` y `origin/main`.
- El PR definitivo exacto ya existía como `#1613` (`development -> main`, draft), pero seguía mostrando dos bloqueos reales:
  - `Documentación automática de PR` fallaba con `GH013` por intentar pushear directo a `development`.
  - `Tests automatizados` fallaba por una regresión funcional en `admisiones` que había perdido el traspaso hacia `AcompanamientoService`.

## Cambios aplicados

- Se restauró en `admisiones/services/admisiones_service/impl.py` el llamado a `AcompanamientoService.importar_datos_desde_admision(admision)`:
  - al disponibilizar acompañamiento, antes de persistir estado parcial;
  - al comenzar acompañamiento desde el flujo legacy.
- Se endureció `.github/workflows/pr-docs.yml` para detectar ramas origen protegidas (`development`, `main`):
  - el workflow sigue generando artefactos;
  - si la rama está protegida, reporta el diff en `GITHUB_STEP_SUMMARY`;
  - ya no intenta `git push` directo y deja de chocar contra `GH013`.
- Se ajustó `scripts/ci/pr_doc_automation.py` para:
  - normalizar paths quoted por git y evitar mojibake/escapes octales en `docs/registro/prs/`;
  - respetar la fecha declarada en el PR de release (`2026-04-23`) antes de caer al cálculo por próximo miércoles.
- Se agregaron tests unitarios para cubrir ambos endurecimientos de `pr_doc_automation.py`.

## Impacto

- El corte `development -> main` queda con una causa raíz menos en CI y con la regresión funcional de `admisiones` encapsulada en un diff chico y revisable.
- La documentación automática de PR pasa a comportarse correctamente con ramas protegidas sin perder trazabilidad del diff generado.
- Los artefactos de release dejan de derivar fechas inconsistentes respecto del PR final solicitado para producción.

## Validación asociada

- Regresiones puntuales de `admisiones`.
- Tests unitarios de `pr_doc_automation`.
- Verificación manual del diff y del workflow `pr-docs` contra el caso real del PR `#1613`.
