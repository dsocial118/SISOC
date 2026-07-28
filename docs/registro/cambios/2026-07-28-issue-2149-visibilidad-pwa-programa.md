# Visibilidad de comedores con programa en PWA

## Fecha

2026-07-28

## Objetivo

Resolver el issue #2149 evitando que la PWA muestre o permita gestionar comedores sin programa asignado.

## Alcance

- Selector, detalle y espacios asignables de la PWA.
- Endpoints PWA que autorizan por comedor, incluida la gestión de nómina.

## Cambios realizados

- El filtro central de visibilidad PWA excluye comedores con `programa IS NULL`, aunque el usuario tenga una asignación activa.
- Se conserva la regla existente para Alimentar Comunidad: solo es visible con estado Activo y proceso En ejecución.
- La misma elegibilidad se reutiliza para IDs accesibles y permisos PWA, por lo que un URL conocido no permite consultar ni gestionar un comedor que dejó de ser visible.
- La evaluación ocurre en cada consulta, por lo que asignar o quitar un programa actualiza automáticamente la disponibilidad en PWA.
- Se agregaron regresiones para lista, detalle, nómina y espacios asignables antes y después de quitar un programa.

## Archivos tocados

- `comedores/api_views.py`
- `users/services_pwa.py`
- Pruebas PWA de comedores, nómina, colaboradores, formación, mensajes y push.

## Validaciones

- 99 pruebas PWA y de formularios de acceso relacionadas.
- `black`, `pylint` y verificación de whitespace.

## Pendientes / riesgos

- No requiere migración ni cambios en el frontend mobile.
