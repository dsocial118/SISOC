# Prestaciones conveniadas y datos sociales de beneficiarios

## Fecha
2026-05-28

## Objetivo
Agregar en Mobile/PWA la consulta y conformidad mensual de prestaciones conveniadas para Alimentar Comunidad, y registrar datos sociales mínimos de beneficiarios: pertenencia a comunidad indígena/pueblo originario y situación de calle.

## Alcance
- Pantalla Mobile de prestaciones conveniadas para espacios de Alimentar Comunidad.
- API de prestaciones alimentarias aprobadas desde el último informe técnico finalizado.
- Historial mensual de conformidad/no conformidad con usuario y fecha.
- Alta y edición limitada de datos sociales de beneficiarios en PWA.
- Visualización de esos datos sociales en detalles Mobile y en el legajo web de ciudadano.

## Archivos tocados
- `comedores/models.py`
- `comedores/migrations/0043_prestacionalimentariaconformidad.py`
- `comedores/api_serializers.py`
- `comedores/api_views.py`
- `pwa/models.py`
- `pwa/migrations/0016_nominaespaciopwa_flags_sociales.py`
- `pwa/api_serializers.py`
- `pwa/services/nomina_service.py`
- `pwa/admin.py`
- `ciudadanos/views.py`
- `ciudadanos/templates/ciudadanos/ciudadano_detail.html`
- `mobile/src/api/prestacionesApi.ts`
- `mobile/src/api/nominaApi.ts`
- `mobile/src/app/router.tsx`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `mobile/src/features/home/SpacePrestacionesConveniadasPage.tsx`
- `mobile/src/features/home/SpaceNominaPersonFormPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPersonFormPage.tsx`
- `mobile/src/features/home/SpaceNominaPersonDetailPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPersonDetailPage.tsx`

## Cambios realizados
- Se creó el modelo `PrestacionAlimentariaConformidad` para guardar conformidad mensual por comedor, informe técnico, usuario y fecha.
- Se expuso API para consultar prestaciones aprobadas del último informe técnico y registrar conformidad/no conformidad mensual.
- La fecha de referencia del informe se toma del historial de estados de admisión cuando el informe pasa a `Informe técnico finalizado`.
- Se agregó pantalla Mobile de prestaciones conveniadas con totales semanales, detalle por día y acciones `Sí`/`No`.
- Se movió el acceso a prestaciones conveniadas dentro de Información Institucional.
- Se agregaron los flags `pertenece_comunidad_indigena` y `situacion_calle` al perfil PWA de nómina.
- La PWA permite marcar esos flags al alta y editarlos luego desde `Editar datos sociales`, sin editar datos personales del beneficiario.
- Los detalles Mobile de beneficiario muestran esos datos sociales.
- El legajo web de ciudadano muestra pueblo originario y situación de calle, y agrega una badge visible junto al nombre cuando está en situación de calle.
- Se extendieron timeouts de detalle/edición de beneficiarios y se desacopló la carga del historial de asistencia para no bloquear la ficha.

## Supuestos
- Los datos sociales se guardan a nivel `NominaEspacioPWA`, no directamente en `Ciudadano`, porque se capturan desde la gestión de beneficiarios Mobile/PWA.
- En el legajo web de ciudadano se informa `Sí` si existe al menos un perfil PWA activo asociado al ciudadano con el flag correspondiente.
- La conformidad de prestaciones es única por comedor y período mensual.

## Validaciones ejecutadas
- `docker compose exec django python manage.py check`: sin issues.
- `docker compose exec django python manage.py makemigrations --check --dry-run`: sin cambios detectados.
- `git diff --check`: sin errores de whitespace.

## Pendientes / riesgos
- La documentación se generó desde un worktree ya iniciado en modo FAST, no desde el arranque seguro dedicado indicado por AGENTS.md.
- La verificación de cambios Mobile por `git -C mobile` quedó bloqueada por configuración local de `safe.directory`; la consistencia se revisó por búsqueda directa de archivos.
- Si se decide que los datos sociales deben ser globales del ciudadano y no del perfil PWA de nómina, hará falta migrarlos o duplicarlos en `Ciudadano`.
