# Security Baseline - PWA (cliente web que consume esta API)

## Alcance

- PWA independiente que consume la API de este backend.
- Aplica a web app, service worker, almacenamiento local y despliegue frontend.

## Controles minimos (checklist)

- [ ] Autenticacion: usar cookies de sesion o tokens segun el backend, sin credenciales hardcodeadas. - Evita exposicion de secretos y reduce superficie de ataque.
- [ ] HTTPS obligatorio en todos los entornos publicados. - Protege credenciales y datos en transito.
- [ ] Almacenamiento: no guardar tokens/PII en `localStorage`. - Reduce riesgo ante XSS o dispositivos compartidos.
- [ ] CSRF: si usa cookies, incluir CSRF token en requests mutating. - Bloquea ataques CSRF en acciones con estado.
- [ ] CSP en frontend: sin `unsafe-eval` y sin `unsafe-inline`. - Mitiga XSS y ejecucion de scripts inyectados.
- [ ] Logs del cliente sin datos sensibles. - Evita fuga de PII en consola o herramientas.

## Estandares de autenticacion y sesion

- El backend actual usa sesiones Django y API Keys (no JWT). - Alinea el esquema de auth del cliente con el backend real.
- Para UI web: cookies httpOnly + CSRF. - Evita exponer tokens al JS y protege acciones sensibles.
- Para integraciones API: API Keys via header, nunca embebidas en el cliente. - Las API Keys son secretas y no deben vivir en frontend.
- Nunca exponer API keys del backend en el cliente.

## Caching y Service Worker

- No cachear endpoints con datos personales o tokens. - Reduce exposicion offline y en disco.
- Cache solo de assets estaticos con versionado. - Asegura integridad y evita contenido stale.
- Invalidar cache en cada release. - Evita que usuarios queden en versiones vulnerables.

## Almacenamiento y PII

- No usar `localStorage`/`IndexedDB` para PII. - Minimiza impacto si hay XSS o acceso local.
- Si se requiere persistencia por requisitos de negocio, cifrar y limitar el alcance. - Reduce el valor de datos filtrados.

## Headers y transporte

- `Strict-Transport-Security` habilitado en prod (servidor frontend). - Fuerza HTTPS y previene downgrade.
- `Content-Security-Policy` estricta en prod. - Limita orígenes de recursos y bloquea inyecciones.
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`. - Evita MIME sniffing y filtra menos referrer.
