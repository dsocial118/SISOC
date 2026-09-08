# Cambio: precarga de provincia en altas de CDI

## Alcance

Al crear una ficha de nómina o un trabajador para un Centro de Desarrollo
Infantil, el formulario selecciona inicialmente la provincia del CDI.

## Comportamiento

- La jurisdicción sigue siendo editable.
- Departamento, municipio y localidad no se precargan; las opciones dependientes
  se cargan desde la provincia inicial mediante la cascada existente.
- La regla también se aplica ante precargas desde RENAPER o un ciudadano para
  evitar combinar una provincia del CDI con valores territoriales de otro origen.
- Las ediciones y los CDIs sin provincia configurada conservan su comportamiento
  anterior.
