# Correcciones de admisiones, PWA y rendiciones

## Fecha
2026-08-10

## Objetivo
Resolver los issues #2076, #2079, #2233, #2234, #2240, #2252 y #2259 sobre admisiones, rendiciones, Informes Técnicos y flujos PWA.

## Alcance
- Admisiones e Informes Técnicos.
- Rendiciones mensuales SISOC–PWA.
- Recuperación de contraseña PWA.
- Certificaciones mensuales de prestaciones.
- Selección de proyectos de organizaciones en PWA.

## Archivos tocados
- `.env.example`, `config/settings.py`
- `admisiones/` (modelos, formularios, servicios, vistas, templates y migraciones 0076/0077)
- `comedores/` (API, servicio PDF, vistas y templates)
- `pwa/files/varios/PRESTACIONES.*.docx`
- `rendicioncuentasmensual/` (modelo, servicios, vistas, tests y migración 0016)
- `users/` (API, autenticación, formularios, vistas y templates)

## Cambios realizados
- Se evita el error 500 al ingresar un número de expediente duplicado y se conserva el error de unicidad en el formulario.
- Se corrige la reapertura de rendiciones subsanadas y se impide validar documentación antes de iniciar su revisión.
- Se amplía el Informe Técnico con los campos y condiciones solicitados en #2233.
- Se incorpora la condición de Informe Complementario con modificación de prestaciones para renovaciones y selección dinámica de templates.
- Se reemplaza el reseteo administrativo por recuperación PWA mediante username, email y enlace configurable por ambiente.
- Se generan certificaciones con cuatro templates según conformidad y usuario principal/subusuario; SISOC muestra el estado y permite filtrar el historial.
- La PWA expone los proyectos activos de la organización y persiste el proyecto seleccionado en la rendición.

## Supuestos
- Los templates dinámicos de Informe Técnico para las nuevas combinaciones serán creados y publicados por usuarios autorizados en cada ambiente.
- `PWA_BASE_URL` se configurará con la URL pública correspondiente a cada ambiente.

## Validaciones ejecutadas
- Se ejecutaron seis pruebas puntuales MySQL del flujo de rendiciones durante la implementación.
- Se verificó manualmente el envío y enlace de recuperación PWA en ambiente local.
- Se verificó en base la persistencia y resolución de la nueva condición del issue #2234.
- Se ejecutaron 158 tests focalizados de admisiones, templates, certificaciones, rendiciones y autenticación: todos aprobados.

## Pendientes / riesgos
- Antes de operar #2234 en producción deben existir versiones publicadas para las combinaciones de templates requeridas.
- Las migraciones 0076, 0077 y 0016 deben aplicarse durante el despliegue.
