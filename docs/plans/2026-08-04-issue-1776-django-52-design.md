# Issue #1776 - Migracion a Django 5.2 LTS

## Objetivo

Migrar SISOC desde Django 4.2.27 a la linea LTS 5.2 sin mezclar el cambio de
framework con incompatibilidades evitables de paquetes o de la interfaz web.

## Estrategia aprobada

La entrega se divide en dos PRs:

1. **Compatibilidad previa sobre Django 4.2**: actualizar el ecosistema a
   versiones que soporten 4.2 y 5.2, corregir APIs deprecadas compatibles con
   ambas lineas y adaptar el logout web a POST con CSRF.
2. **Cambio de framework**: fijar el ultimo parche 5.2 disponible, resolver las
   incompatibilidades exclusivas de 5.x y ejecutar la validacion integral.

Este corte permite revertir el segundo PR a Django 4.2 sin deshacer las
correcciones ni los paquetes preparados en el primero.

## Contratos funcionales

- El logout web no debe ejecutarse mediante GET.
- Todos los controles visibles de logout deben enviar POST con token CSRF.
- Importacion y exportacion desde admin conservan CSV/XLSX, preview obligatorio
  y confirmacion separada.
- Autenticacion DRF, API keys, auditoria y OpenAPI conservan sus contratos.
- La migracion no debe generar cambios de modelos inesperados ni reescribir
  migraciones historicas.

## Dependencias

El primer PR usa versiones con soporte declarado simultaneo para Django 4.2 y
5.2. `django-select2`, `django-multiselectfield` y `django-appconf` se retiran
porque no tienen imports ni modelos consumidores en el repositorio. El
resolver y la suite deben confirmar la eliminacion.

`django-import-export` pasa a 4.x y requiere atencion especial por sus cambios
de API y de renderizado. Los tests existentes de admin son el contrato de
regresion principal.

## Validacion

### PR 1

- Resolver limpio de `requirements.txt` con Django 4.2.
- Tests de logout, import/export, APIs, auditoria y wizard VAT.
- Suite completa con deprecaciones visibles.
- `check`, `makemigrations --check --dry-run`, lint y CI obligatorio.

### PR 2

- Resolver limpio con el ultimo Django 5.2.x.
- `check --deploy`, suite completa SQLite y `mysql_compat` real.
- Revision de migraciones propias y de terceros.
- Generacion/validacion OpenAPI y `collectstatic`.
- Smoke en QA de login/logout, admin import/export, auditoria, APIs y formularios.

## Despliegue y rollback

El merge a `development` despliega QA. La promocion posterior queda fuera de
ambos PRs hasta contar con CI y smoke de QA. Si el segundo PR falla, se revierte
el pin de Django; el primer PR permanece por ser compatible con 4.2.
