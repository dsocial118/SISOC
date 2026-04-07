# Login web: fix de CSP, pylint y formato

## Contexto

Durante la validación automática del login web se detectaron tres problemas:

- un script inline sin `nonce` en el template de login;
- un warning de `pylint` por la firma de `__init__` en `BackofficeAuthenticationForm`;
- diferencias de formato que `black` reescribe en archivos del flujo de login y
  de importación de Celiaquía.

## Cambio realizado

- Se agrega `nonce="{{ request.csp_nonce }}"` al script inline del login.
- Se reordena la firma de `BackofficeAuthenticationForm.__init__` para que `pylint`
  no marque `keyword-arg-before-vararg`.
- Se ajusta el orden de imports en `celiaquia/services/importacion_service/impl.py`
  para que coincida con `black`.

## Impacto

- No cambia el comportamiento funcional del login.
- Se mantiene el soporte CSP del template.
- Se deja el código en estado compatible con los checks de CI.
