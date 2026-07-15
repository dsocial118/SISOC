# Plan A: autoaprobacion de sincronizaciones descendentes

El workflow `sync-main-downstream.yml` ahora aprueba con su `GITHUB_TOKEN` el
PR exacto que abre o reutiliza desde `main` hacia `development` u
`homologacion`, antes de intentar el merge.

Esto satisface la regla de revision obligatoria de `development` sin ampliar el
alcance a PRs con otra rama de origen. Requiere que el repositorio permita a
GitHub Actions crear y aprobar pull requests.
