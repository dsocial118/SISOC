# Artefactos de PR en promociones desde ramas protegidas

`pr-docs.yml` ahora informa, sin bloquear, los artefactos spec-as-source que
falten en un PR interno cuyo origen sea `development`, `homologacion` o `main`.
La advertencia queda en el Summary del workflow con los paths y el comando de
generación correspondiente.

Los PRs desde ramas de trabajo o forks mantienen el gate estricto. Así se evita
que una promoción quede bloqueada porque GitHub Actions no puede escribir su
rama protegida, sin ocultar la falta de artefactos cuando el workflow sí puede
generarlos.
