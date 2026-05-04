# Estabilización de Capacitaciones Web y Cursos en Mobile

## Fecha
2026-05-01

## Objetivo
Corregir inconsistencias funcionales en Web y Mobile: evitar cambios de estado inválidos en certificados de capacitaciones y mejorar la navegación de Cursos en PWA con fallback robusto.

## Alcance
Se incluyeron ajustes en backend/plantilla web de capacitaciones y en módulos de hub/ruteo/vistas mobile para Cursos y textos con acentos en formulario de beneficiarios.

## Archivos versionados tocados
- comedores/services/capacitaciones_certificados_service.py
- comedores/templates/comedor/comedor_detail.html

## Referencias operativas fuera del diff versionado
La carpeta `mobile/` está ignorada por git en este repositorio. Estos archivos documentan el cierre funcional de la rama `SiSOC-Mobile-29-04`, pero no se entregan como archivos versionados dentro de este PR a `main`:
- mobile/src/features/home/SpaceHubPage.tsx
- mobile/src/features/home/SpaceCursosPage.tsx
- mobile/src/app/router.tsx
- mobile/src/ui/AppLayout.tsx
- mobile/src/features/home/SpaceNominaPersonFormPage.tsx

## Cambios realizados
- Se bloqueó en servicio web la transición entre estados finales de certificados (`aceptado`/`rechazado`) una vez revisados.
- Se deshabilitaron en UI web los botones de aceptar/rechazar cuando el certificado está en estado final.
- Se habilitó el módulo `Cursos` en hub mobile para espacios de `Alimentar Comunidad`.
- Se creó pantalla interna de `Cursos` en mobile con carga embebida (iframe).
- Se agregó fallback automático: si el iframe no carga, abre enlace en navegador externo.
- Se agregó botón visible de `Abrir en navegador` con ícono de salida externa.
- Se configuró header de mobile para mostrar título `Cursos` en la ruta correspondiente.
- Se corrigieron textos mojibake/acentos en alta de beneficiarios (`nomina/nueva`).

## Supuestos
- El bloqueo funcional esperado para certificados es no permitir alternar entre estados finales después de una revisión.
- El sitio externo de Cursos puede tener restricciones de CORS/X-Frame; por eso se requiere fallback a navegador.

## Validaciones ejecutadas
- `npm run build` en `mobile/` (OK).
- Verificación de presencia de rutas y referencias de `Cursos` en hub/router/layout (OK).

## Pendientes / riesgos
- Si el sitio de Cursos bloquea iframe por políticas del servidor, siempre se activará el fallback externo.
- Persisten en la rama cambios no relacionados previos a este cierre (fuera del alcance de este registro).
