# CONTRIBUTING_AI.md

Proceso recomendado para trabajar con IA en SISOC.

Fuente de verdad:
- `../../AGENTS.md`

## Brief recomendado

Todo pedido deberia incluir:
- contexto,
- objetivo,
- alcance,
- restricciones,
- criterio de aceptacion,
- validacion esperada,
- si se permiten mejoras cercanas.

## Lectura minima antes de implementar

No hace falta leer `docs/ia/*` completo.

Base obligatoria:
1. `AGENTS.md`
2. `docs/indice.md`
3. archivo objetivo
4. tests del modulo
5. una sola guia relevante de `docs/ia/`

Ampliar solo si el cambio lo exige.

## Flujo sugerido

1. Explorar el codigo real del modulo.
2. Delimitar el diff minimo.
3. Implementar alineado al patron existente.
4. Validar primero con checks puntuales.
5. Documentar cambios importantes en `docs/` si aplica.
6. Entregar con resumen, validacion, supuestos y riesgos.

## Reglas de PR y commits

- Una sola intencion principal por PR.
- Mensaje de commit en espanol.
- Primera linea con patron `<type>(<scope>): <subject>`.

Tipos frecuentes:
- `fix`
- `feat`
- `refactor`
- `test`
- `docs`
- `chore`

## Validacion recomendada

Secuencia corta:
1. formateo o lint de archivos editados,
2. tests del modulo o flujo afectado,
3. checks mas amplios solo si hace falta.

## Spec-as-source

Registrar en `docs/`:
- cambios funcionales visibles,
- decisiones de diseno,
- cambios de seguridad o permisos,
- trade-offs relevantes.

Si no aplica, explicitarlo en la entrega.
