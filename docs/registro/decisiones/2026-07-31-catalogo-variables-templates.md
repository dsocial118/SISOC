# Decisión: las variables del template se habilitan desde un catálogo persistido

## Contexto

Los modelos DOCX vigentes contienen decenas de expresiones Django. Exponerlas
solamente como texto libre haría fácil introducir un nombre inválido y obligaría
a recordar su sintaxis técnica.

## Decisión

Se crea `VariableTemplateInformeTecnico` como catálogo persistido. Cada fila
guarda el código de expresión sin delimitadores, un nombre entendible, categoría,
orden y estado activo. El editor inserta el token completo y la publicación
verifica el estado del catálogo.

## Consecuencias

- Las 106 expresiones actuales se conservan sin renombrarlas, por lo que siguen
  siendo compatibles con el contexto de generación existente.
- También se registran los alias planos históricos del contexto (por ejemplo,
  `nombre_espacio`), para conservar los borradores realizados en la primera
  versión del Gestor.
- El Gestor de templates puede retirar temporalmente una variable de nuevos
  contenidos sin alterar los datos de una admisión.
- Una nueva variable debe agregarse junto con la implementación que garantice
  su valor en el contexto de generación; no se puede crear arbitrariamente
  desde la pantalla.
