# 2026-05-06 - Predeploy development a main

## Contexto

Se preparo el corte `development -> main` con worktree aislada desde
`origin/development`, comparando el diff real contra `origin/main`.

## Cambios de saneamiento

- Se actualizo el bloque superior de `CHANGELOG.md` para reflejar el corte de
  release del 2026-05-06, tomando como fuente los cambios documentados en
  `docs/registro/cambios/` y el diff `origin/main..origin/development`.
- Se declaro `serializer_class` en el endpoint PWA de Formacion para que la
  generacion OpenAPI no quede ambigua en el nuevo `CursoAppMobilePWAViewSet`.

## Impacto

El saneamiento no cambia reglas de negocio. El endpoint PWA conserva la misma
respuesta y el changelog queda listo para que el PR final exacto
`development -> main` muestre el alcance funcional de la promocion.

## Validacion esperada

- `python manage.py makemigrations --check --dry-run`
- `python manage.py check`
- `python manage.py spectacular --file /tmp/schema.yml --validate`
- Tests focalizados del endpoint PWA de Formacion y del generador de changelog.
