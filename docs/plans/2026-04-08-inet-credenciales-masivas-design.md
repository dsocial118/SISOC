# 2026-04-08 - Diseno de tipos de envio para credenciales masivas

## Objetivo

Extender el flujo de envio masivo de credenciales en `users` para soportar variantes de negocio sin duplicar pantalla, permisos ni servicios base.

## Decision

- Mantener una sola pantalla web.
- Agregar un desplegable `tipo_envio`.
- Resolver plantilla Excel, columnas requeridas, subject y template de correo desde un registro backend por tipo.

## Tipos iniciales

### Estandar
- Columnas: `usuario`, `mail`, `password`
- Subject: `SISOC - Credenciales de acceso`
- Template: correo simple con credenciales y cambio obligatorio al primer ingreso

### INET
- Columnas: `usuario`, `mail`, `password`, `Nombre del Centro`
- Subject: `Acceso a la plataforma y capacitacion virtual - INET`
- Template: correo especifico con nombre del centro, acceso a SISOC, sesiones de capacitacion y video de referencia

## Impacto en UX

- El operador elige el tipo en un desplegable.
- El boton `Descargar plantilla` usa ese tipo para bajar el Excel correcto.
- El boton `Enviar credenciales` procesa el archivo usando las reglas del tipo elegido.
- La pantalla lista los tipos disponibles y sus columnas esperadas para evitar errores sin agregar preview ni JS custom.

## Validacion prevista

- Tests de descarga de plantilla por tipo.
- Tests de procesamiento del flujo estandar y del flujo INET.
- Test de validacion por columna extra requerida en INET.
- Test de la view para asegurar que el dropdown participa del submit.
