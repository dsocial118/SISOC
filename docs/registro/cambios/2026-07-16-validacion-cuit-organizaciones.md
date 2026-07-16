# Validación de CUIT en organizaciones

## Cambio

El alta y la edición de organizaciones aceptan el CUIT únicamente cuando contiene
11 dígitos numéricos, sin símbolos ni espacios. La interfaz restringe la entrada y
el formulario Django conserva la validación del lado servidor.

## Alcance

La regla se define en `OrganizacionForm`, compartido por los tres tipos de entidad:

- Personería jurídica.
- Personería jurídica eclesiástica.
- Asociación de hecho.

El control de CUIT duplicado se ejecuta solamente cuando la entrada ya tiene el
formato válido de 11 dígitos.

## Compatibilidad

El campo continúa siendo opcional y no cambia el esquema de base de datos.
