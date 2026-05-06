# VAT referentes multiples y CFPRevisor

## Contexto

El issue #1682 cambia la asignacion de centros VAT desde un unico referente a una relacion N:N de referentes, y agrega revisores asignables por centro.

## Decision

- `Centro.referentes` es la relacion canonica para usuarios CFP que gestionan un centro.
- `Centro.revisores` es la relacion canonica para usuarios CFPRevisor que solo visualizan centros asignados.
- `Centro.referente` queda como FK legacy sincronizada con el primer referente para no cortar serializers, importadores y comandos existentes.
- CFPINET mantiene su comportamiento previo.

## Impacto

- Alta y edicion de centros muestran `Referente/s` obligatorio y `Usuario Revisor` opcional.
- El legajo de centro muestra todos los referentes y no expone revisores.
- Los scopes de lectura unen referentes y revisores; los scopes de gestion excluyen revisores.
- Los importadores legacy con `referente_id` siguen funcionando y sincronizan el M2M.
