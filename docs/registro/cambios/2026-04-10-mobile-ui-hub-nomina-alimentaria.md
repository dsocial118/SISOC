# Mobile — ajustes UI SpaceHubPage y SpaceNominaAlimentariaPage

**Fecha:** 2026-04-10
**Archivos tocados:**
- `mobile/src/features/home/SpaceHubPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`

## Qué cambió

### SpaceHubPage — mensaje "sin programa" sin card y centrado

El mensaje que aparece cuando un espacio no tiene programa definido estaba dentro de un `<div>`
con estilos de card (`rounded-2xl border p-5`).

**Cambio:** se reemplazó el `<div>` por un `<p>` con `text-center` y color según tema
(`text-white` dark / `text-slate-700` light). El punto entre las dos oraciones se convirtió en
punto y aparte con `<br />`.

Texto resultante:
```
No hay programa definido.
Comuníquese con un administrador de la aplicación.
```

### SpaceNominaAlimentariaPage — cards de stats sin gradiente

Las cards de Asistentes, Género y Edades usaban `linear-gradient(45deg, #232D4F 0%, #585697 100%)`
con sombra fija y textos/íconos hardcodeados en `text-white`, ignorando el modo claro.

**Referencia usada:** `SpaceActivitiesPage` — patrón real de la app sin gradiente:
- `cardStyle`: `backgroundColor: '#232D4F'` (dark) / `'#F5F5F5'` (light), sombra `4px 4px 4px rgba(0,0,0,0.25)`
- Borde `#E7BA61` (amarillo de la app)
- Textos e íconos usando `textClass` y `detailTextClass` para respetar light/dark mode

**Cambios:**
- Las 3 cards usan `cardStyle` + `summaryCardClass` (fondo según tema) + `borderColor: '#E7BA61'`
- Todos los `text-white` hardcodeados reemplazados por `textClass` / `detailTextClass`
- `summaryCardClass` restaurado solo con el fondo (sin color de texto, que viene de `textClass`)
- Se eliminó la sombra `shadow-[0_8px_18px_rgba(35,45,79,0.28)]` que era parte del gradiente

## Resultado

- Light mode: cards con fondo `#F5F5F5`, textos `#232D4F`, borde amarillo.
- Dark mode: cards con fondo `#232D4F`, textos blancos, borde amarillo.
- Consistente con el resto de las páginas de la app mobile.
