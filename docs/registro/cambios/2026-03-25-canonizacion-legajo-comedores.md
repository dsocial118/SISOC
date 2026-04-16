# 2026-03-25 - Canonización del legajo principal de comedores

## Resumen
- El detalle principal de comedores quedó canonizado en `comedor_detalle` (`/comedores/<pk>`).
- La URL legacy `/comedores_nuevo/<pk>` ahora responde con redirección permanente `301` hacia la ruta canónica.
- Se retiró el template viejo/experimental del detalle de comedor y se promovió la UI nueva como única implementación activa.
- No se migraron al detalle principal las acciones inline de relevamientos; el legajo ahora deriva ese flujo al módulo de relevamientos.
- Se preservó en el detalle canonizado el acceso a la nómina directa para programas que no usan admisión.

## Cambios realizados
- Archivo: `comedores/templates/comedor/comedor_detail.html`
  - Se reemplazó el detalle legacy por la UI moderna canonizada.
  - Se normalizaron todos los `next` y referencias internas para volver a `comedor_detalle`.
  - Se mantuvo visible el acceso al módulo de relevamientos sin reintroducir alta/edición inline.
  - Se portó el CTA de `nomina_directa_ver` y el aviso informativo para programas con nómina directa.
- Archivo: `comedores/urls.py`
  - `comedor_detalle` se mantiene como contrato principal.
  - `nuevo_comedor_detalle` pasó a ser un alias legacy con `RedirectView` permanente.
- Archivo: `comedores/views/comedor.py`
  - `ComedorDetailView.post()` dejó de procesar relevamientos desde el detalle y vuelve al legajo canónico para POSTs no soportados.
- Archivo: `comedores/services/comedor_service/impl.py`
  - Se eliminó la lógica específica de relevamientos acoplada al detalle viejo.
- Archivo: `templates/includes/sidebar/new_opciones.html`
  - Se ajustó la activación visual del menú para usar la ruta canónica de comedores.

## Assets y cleanup
- Se creó `static/custom/css/comedor_detail.css` como asset canónico del detalle principal.
- Se eliminó `comedores/templates/comedor/new_comedor_detail.html`.
- Se removieron referencias activas a `nuevo_comedor_detalle` dentro del flujo principal del legajo.

## Validación esperada
- `GET /comedores/<pk>` renderiza el legajo principal canonizado.
- `GET /comedores_nuevo/<pk>` responde `301` hacia `/comedores/<pk>`.
- El detalle ya no contiene referencias HTML activas a `nuevo_comedor_detalle` ni a `comedores_nuevo/`.
- Los programas sin admisión siguen exponiendo el acceso a la nómina directa desde el detalle principal.
