# Cambios en el Módulo de Celiaquia

## Resumen de Cambios

Se implementaron las siguientes modificaciones en el módulo de celiaquia según los requerimientos:

### 1. Eliminación del Documento DNI (archivo1)

- **Antes**: Las provincias debían enviar 3 documentos por persona (DNI, Biopsia/Constancia médica, Negativa ANSES)
- **Después**: Las provincias solo deben enviar 2 documentos (Biopsia/Constancia médica, Negativa ANSES)

#### Archivos modificados:
- `celiaquia/models.py`: Actualizado `_recompute_archivos_ok()` y métodos relacionados
- `celiaquia/services/legajo_service.py`: Actualizado para manejar solo 2 archivos
- `celiaquia/views/expediente.py`: Actualizado validaciones de archivos faltantes
- `celiaquia/views/legajo.py`: Actualizado carga de archivos
- `celiaquia/templates/celiaquia/expediente_detail.html`: Removido archivo1 del template
- `static/custom/js/expediente_detail.js`: Actualizado mapeo de slots

### 2. Botón "Validación Renaper" para Técnicos

- **Funcionalidad**: Los técnicos ahora pueden validar los datos del ciudadano contra Renaper
- **Ubicación**: Botón agregado junto a las acciones de revisión (Aprobar, Subsanar, Rechazar)
- **Acceso**: Solo técnicos y coordinadores pueden usar esta funcionalidad

#### Archivos creados/modificados:
- `celiaquia/views/validacion_renaper.py`: Nueva vista para validación Renaper
- `celiaquia/urls.py`: Nueva ruta para validación Renaper
- Template: Agregado modal de validación con comparación lado a lado
- JavaScript: Funcionalidad para mostrar comparación de datos

### 3. Popup de Comparación Provincia vs Renaper

- **Diseño**: Modal con dos columnas mostrando datos provinciales vs datos de Renaper
- **Campos comparados**:
  - DNI
  - Nombre
  - Apellido
  - Fecha de nacimiento
  - Sexo
  - Dirección (calle, altura, piso/departamento)
  - Ciudad
  - Provincia
  - Código postal
- **Indicadores visuales**: Campos que coinciden se muestran en verde, los que difieren en amarillo

## Migración de Base de Datos

Se creó la migración `0003_remove_dni_requirement.py` que:
- Actualiza el campo `archivos_ok` para todos los registros existentes
- Recalcula basándose solo en archivo2 y archivo3
- Incluye función de reversión

## Integración con Renaper

La validación utiliza el servicio existente de Renaper (`ciudadanos/services/consulta_renaper.py`) que:
- Autentica con las credenciales configuradas en `.env`
- Consulta datos por DNI y sexo
- Maneja errores de conexión y personas fallecidas
- Mapea provincias correctamente

## Configuración Requerida

Las siguientes variables de entorno deben estar configuradas:
```
RENAPER_API_USERNAME=ssph-sisoc@secretarianaf.gob.ar
RENAPER_API_PASSWORD=Sisoc2025*
RENAPER_API_URL=https://wsv2.secretarianaf.gob.ar/api
```

## Permisos

- **Validación Renaper**: Solo técnicos (`TecnicoCeliaquia`) y coordinadores (`CoordinadorCeliaquia`)
- **Carga de archivos**: Provincias pueden cargar solo archivo2 y archivo3
- **Revisión de legajos**: Sin cambios en permisos existentes

## Notas Técnicas

1. El campo `archivo1` se mantiene en la base de datos por compatibilidad, pero ya no se usa en validaciones
2. La funcionalidad es retrocompatible con expedientes existentes
3. Los métodos del modelo se actualizaron para reflejar el nuevo requerimiento de 2 archivos
4. El JavaScript maneja errores de conexión con Renaper de forma elegante

## Testing

Para probar los cambios:
1. Crear un expediente nuevo y verificar que solo requiere 2 archivos
2. Como técnico, usar el botón "Validación Renaper" en un legajo
3. Verificar que la comparación muestre datos correctamente
4. Confirmar que expedientes existentes siguen funcionando

## Rollback

Si es necesario revertir los cambios:
1. Ejecutar la migración reversa: `python manage.py migrate celiaquia 0002`
2. Revertir los cambios en el código usando git
3. Los datos no se perderán, solo se recalculará `archivos_ok`