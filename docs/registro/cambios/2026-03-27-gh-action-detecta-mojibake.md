# GH Action para detectar mojibake

## Contexto

Se detectaron regresiones de codificacion en textos del repositorio por interpretaciones incorrectas de UTF-8.

## Cambio aplicado

Se agrego el job `encoding_check` en [lint.yml](C:/Users/Juanito/Desktop/Repos-Codex/SISOC/.github/workflows/lint.yml).

### Que hace

- Recorre solo los archivos de texto cambiados en el PR o push actual.
- Intenta leerlos como UTF-8.
- Ignora binarios y directorios no relevantes (`.git`, `node_modules`, `media`, `staticfiles`, etc.).
- Falla si encuentra patrones tipicos de mojibake asociados a acentos, eñes, signos invertidos y comillas tipograficas rotas.

## Integracion con CI

Se agrego `encoding_check` a la lista de checks requeridos del `deploy_guard` en [tests.yml](C:/Users/Juanito/Desktop/Repos-Codex/SISOC/.github/workflows/tests.yml), para que el PR no pueda considerarse conforme si aparece texto corrupto.

## Alcance y limite

El check detecta patrones comunes de mojibake, no reemplaza una politica completa de encoding del repositorio. Su funcion es preventiva y de bloqueo temprano en PRs.
