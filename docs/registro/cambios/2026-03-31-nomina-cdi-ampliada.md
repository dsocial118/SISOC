# Nómina CDI ampliada

Fecha: 2026-03-31

## Qué cambió

- Se amplió `NominaCentroInfancia` para guardar la ficha específica de CDI:
  - datos personales
  - pertenencia a pueblo originario
  - desarrollo y salud
  - domicilio
  - responsables legales
  - persona adulta responsable
- Se mantuvo la búsqueda por DNI y la precarga desde RENAPER.
- Cuando el DNI ya existe en `Ciudadano`, la nómina CDI ahora abre la ficha completa sobre ese ciudadano en lugar de hacer un alta rápida.
- Cuando el DNI no existe y RENAPER responde, la ficha se precarga y desde ahí se crea el `Ciudadano` mínimo necesario para sostener la FK.
- La vista de nómina muestra DNI, sexo, edad y sala usando los datos propios de la ficha CDI, con fallback al ciudadano global cuando todavía no existan datos migrados.

## Decisión de diseño

- Los campos nuevos se guardan en `NominaCentroInfancia` y no en `Ciudadano`.
- Motivo:
  - la información pedida es específica del flujo CDI
  - reduce impacto lateral sobre otros módulos que consumen `Ciudadano`
  - permite conservar una ficha CDI por alta de nómina sin redefinir el padrón global

## Reglas incorporadas

- `¿Cuál?` de pueblo originario solo aplica cuando la respuesta anterior es `Si`.
- El detalle de discapacidad y el campo de apoyo actual solo aplican cuando la respuesta de discapacidad es `Si`.
- Provincia, municipio y localidad del domicilio validan consistencia jerárquica.
- Edad se calcula desde la fecha de nacimiento y no se persiste como dato independiente.

## Validación

- Se agregaron tests puntuales para:
  - duplicados en la nómina
  - validación condicional de pueblo originario
  - cálculo de edad en el formulario
  - creación de ficha CDI para un ciudadano existente

## Limitaciones actuales

- No fue posible ejecutar `manage.py makemigrations` ni `pytest` en este entorno porque `django` no está instalado localmente.
- La migración `0021_expandir_nomina_cdi.py` quedó escrita manualmente y debe validarse en el entorno habitual del proyecto antes de mergear.
