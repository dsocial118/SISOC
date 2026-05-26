# 2026-05-19 — VAT: wizard de 3 pasos para crear Comisión de Curso

## Resumen
El flujo principal de creación de comisiones migra a una página dedicada estilo
wizard de 3 pasos, fiel al mockup acordado con producto. El botón "+ Comisión"
del listado de cursos ahora navega a esta URL.

El modal `#modalComisionCurso` se conserva para el flujo secundario "Guardar y
crear comisión" del modal de cursos (post-create action). La edición también
sigue usando modal (no cambia).

## Alcance
- **Paso 1 — Información básica**: ubicación, cupo total (5-100), estado,
  fecha de inicio (≥ hoy), fecha de finalización (> fecha de inicio),
  observaciones. El curso ya viene fijado por la URL.
- **Paso 2 — Horarios de clase**: formset dinámico de `ComisionHorario`
  (día, hora inicio, hora fin, estado). El estado se mapea a `vigente bool`
  (`"1"` → True, `"0"` → False). Reglas: ≥ 1 horario, duración 45 min – 4 h,
  total semanal ≥ 2 h, sin días repetidos. El contador "Total semanal" se
  recalcula en cliente.
- **Paso 3 — Confirmación**: resumen agrupado (Curso · Comisión · Horarios) y
  submit transaccional.

## Componentes
- `VAT/forms.py`
  - `ComisionCursoWizardStep1Form`
  - `ComisionCursoWizardHorarioForm`
  - `BaseComisionCursoWizardHorarioFormSet`
  - `ComisionCursoWizardStep2FormSet` (factory)
  - `ComisionCursoWizardStep3Form` (vacío, sólo confirma)
- `VAT/views/comision_curso_wizard.py` — `ComisionCursoWizardView`
  (`SessionWizardView` de `django-formtools`, `done()` transaccional).
- `VAT/urls.py` — nueva URL
  `vat/cursos/<int:curso_id>/comision/nueva/` → `vat_comision_curso_wizard`.
- Templates en `VAT/templates/vat/comision_curso_wizard/`
  - `_base.html` (layout + CSS embebido)
  - `_horario_block.html` (fragmento reutilizado por step2 + template clonable)
  - `step1_info.html`, `step2_horarios.html`, `step3_confirmacion.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`: el botón
  "+ comisión" del listado de cursos ahora navega a la URL del wizard
  (antes abría `#modalComisionCurso`).

## Dependencias / config
- `requirements/base.txt`: agregada `django-formtools==2.5.1`.
- `config/settings.py`: agregada `"formtools"` en `INSTALLED_APPS`.

Tras un `git pull` hay que correr `pip install -r requirements.txt` para
que el wizard funcione.

## Permisos
- Acceso protegido por `permissions_any_required(["VAT.add_comisioncurso"])`
  en URL + `can_user_edit_centro` en `dispatch`.

## Pendientes / decisiones diferidas
- La edición de comisiones sigue por modal — se decidió mantener para acotar
  blast radius. Se puede migrar al wizard en otra iteración.
- El estado del horario se persiste sólo como `vigente bool`; si se necesita
  más granularidad (planificado/activo/suspendido) habrá que migrar el modelo.
- `SessionWizardView` mantiene el estado en sesión por nombre de vista; si el
  usuario abandona y vuelve a entrar verá la última data ingresada hasta que
  la sesión expire o termine `done()`.
