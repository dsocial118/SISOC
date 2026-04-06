# Mobile: hub inicial de rendición con cards simples y loading unificado

Fecha: 2026-03-30

## Qué cambió

- El hub inicial de rendición se mantiene dividido en dos bloques: `Nueva rendición` arriba y `Rendiciones creadas` abajo.
- En el historial aparece una card por cada rendición creada, sin contenedores intermedios por organización o proyecto.
- Cada card muestra sólo convenio, número de rendición, estado, fecha de creación y el acceso al detalle.
- Mientras carga el historial, ya no aparece una card con texto plano: se usa el spinner compartido de la app con skeletons del listado.

## Implementación

- El selector de organización y proyecto sigue siendo exclusivo para iniciar una nueva rendición.
- Las rendiciones existentes se siguen cargando automáticamente al entrar al hub.
- Se conserva el contexto interno de cada rendición para navegar al detalle correcto, aunque ese contexto ya no se renderiza en pantalla.
- El estado de carga del historial reutiliza `AppLoadingSpinner` y placeholders `skeleton-shimmer` para mantener consistencia con el resto del mobile.

## Validación

- `npm run build` en `mobile/`
