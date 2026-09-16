# Informes Técnicos de Admisiones

## Alcance

El Informe Técnico concentra los datos de admisión usados por las plantillas
DOCX. Los formularios validan las condiciones del dominio antes de renderizar y
conservan errores de unicidad como errores de formulario, sin responder 500.

## Renovaciones y prestaciones

Las renovaciones pueden requerir un Informe Técnico Complementario cuando se
modifican prestaciones. Esa condición se persiste en Admisiones y se expone
como variable documental para la plantilla; no debe resolverse solo en el
template ni inferirse después de guardar.

Los formularios base y jurídico, tanto de creación como de edición, ya no
solicitan ni validan los campos `monto_total_conveniado_informe` y
`monto_total_conveniado`. Se retiró la sección "Monto total conveniado".
Los valores históricos y las variables documentales se conservan; este cambio
no modifica las plantillas publicadas ni requiere una migración.
Ver `docs/registro/cambios/2026-09-11-informes-tecnicos-sin-monto-conveniado.md`.

## Templates dinámicos

Las combinaciones de condiciones se resuelven mediante versiones publicadas de
templates dinámicos. Solo personal autorizado publica una versión y únicamente
las variables documentales activas quedan disponibles. Antes de habilitar una
combinación nueva en un ambiente, debe existir su template publicado: no se
crea ni publica automáticamente durante el alta de una admisión.

## Despliegue y compatibilidad

Aplicar las migraciones `admisiones.0076`, `0077` y `0078` antes de operar los
nuevos campos. Luego verificar una renovación sin modificación de prestaciones
y otra que requiera informe complementario, incluyendo la resolución de la
plantilla publicada. El rollback de aplicación conserva los datos agregados;
no borrar templates ni valores ya persistidos.

## Referencias

- `admisiones/forms/admisiones_forms.py`
- `admisiones/services/docx_service/impl.py`
- `admisiones/services/templates_informe_tecnico_service/impl.py`
- `docs/registro/cambios/2026-08-10-fixes-admisiones-pwa-rendiciones.md`
- `docs/registro/cambios/2026-08-12-correcciones-issues-reabiertos.md`
