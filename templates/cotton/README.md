# Componentes Cotton - SISOC Backoffice

Esta carpeta contiene los componentes reutilizables creados con Django Cotton para el proyecto SISOC-Backoffice.

## Componentes Disponibles

### 1. `search_bar.html` - Barra de Búsqueda
Componente reutilizable para barras de búsqueda con botones de acción.

**Parámetros:**
- `titulo` (opcional): Título de la barra de búsqueda. Default: "Buscar"
- `placeholder` (opcional): Texto placeholder del input. Default: "Buscar"
- `help_text` (opcional): Texto de ayuda en el title del input
- `reset_url`: URL para el botón "Resetear"
- `add_url` (opcional): URL para el botón "Agregar"
- `show_add_button` (opcional): Mostrar/ocultar botón agregar. Default: True
- `query` (opcional): Valor actual de la búsqueda
- `add_text` (opcional): Texto del botón agregar. Default: "Agregar"

**Ejemplo:**
```django
{% load cotton %}
{% c "search_bar" titulo="Buscar Ciudadano" placeholder="Ingrese DNI o apellido" reset_url=reset_url add_url=add_url query=query %}
```

### 2. `pagination.html` - Paginación
Componente para paginación consistente.

**Parámetros:**
- `is_paginated`: Boolean si está paginado
- `page_obj`: Objeto de página de Django
- `page_range` (opcional): Rango de páginas personalizado
- `query` (opcional): Query de búsqueda para mantener en la paginación
- `prev_text` (opcional): Texto botón anterior. Default: "Volver"
- `next_text` (opcional): Texto botón siguiente. Default: "Continuar"

**Ejemplo:**
```django
{% c "pagination" is_paginated=is_paginated page_obj=page_obj page_range=page_range query=query %}
```

### 3. `breadcrumb.html` - Migas de Pan
Componente para navegación breadcrumb.

**Parámetros:**
- `items`: Lista de diccionarios con estructura:
  ```python
  [
      {"text": "Inicio", "url": "/"},
      {"text": "Sección", "url": "/seccion/"},
      {"text": "Página Actual", "active": True}
  ]
  ```
- `class` (opcional): Clases CSS adicionales

**Ejemplo:**
```django
{% c "breadcrumb" items=breadcrumb_items %}
```

### 4. `delete_confirm.html` - Confirmación de Eliminación
Componente para páginas de confirmación de eliminación.

**Parámetros:**
- `object_name`: Nombre del objeto a eliminar
- `title` (opcional): Título del mensaje. Default: "Atención!"
- `message` (opcional): Mensaje personalizado
- `warning_items` (opcional): Lista de advertencias
- `warning_message` (opcional): Mensaje de advertencia personalizado
- `cancel_url`: URL para cancelar
- `confirm_text` (opcional): Texto botón confirmar. Default: "Eliminar"
- `cancel_text` (opcional): Texto botón cancelar. Default: "Cancelar"

**Ejemplo:**
```django
{% c "delete_confirm" object_name=object warning_items=relaciones_existentes cancel_url=cancel_url %}
```

### 5. `action_buttons.html` - Botones de Acción
Componente para grupos de botones de acción.

**Parámetros:**
- `back_button` (opcional): Diccionario con configuración del botón volver
- `buttons`: Lista de diccionarios con configuración de botones
- `container_class` (opcional): Clases CSS del contenedor
- `buttons_container_class` (opcional): Clases CSS del contenedor de botones

**Ejemplo:**
```django
{% c "action_buttons" back_button=back_button buttons=action_buttons %}
```

### 6. `info_card.html` - Tarjeta de Información
Componente flexible para tarjetas de información.

**Parámetros:**
- `title` (opcional): Título de la tarjeta
- `icon_value_style` (opcional): Estilo icono + valor
- `list_style` (opcional): Estilo de lista de datos
- `card_class` (opcional): Clases CSS de la tarjeta
- `header_class` (opcional): Clases CSS del header
- `body_class` (opcional): Clases CSS del body
- Varios otros parámetros según el estilo usado

### 7. `form_stepper.html` - Stepper de Formularios
Componente para formularios multi-paso.

**Parámetros:**
- `steps`: Lista de pasos con configuración

### 8. `form_buttons.html` - Botones de Formulario
Componente para botones de formulario estandarizados.

**Parámetros:**
- `cancel_button` (opcional): Configuración botón cancelar
- `buttons`: Lista de botones del formulario

## Uso en las Vistas

Para usar estos componentes, las vistas deben proporcionar los datos en el formato correcto:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
        "breadcrumb_items": [
            {"text": "Inicio", "url": reverse("home")},
            {"text": "Sección", "active": True}
        ],
        "reset_url": reverse("lista"),
        "add_url": reverse("crear"),
    })
    return context
```

## Instalación y Configuración

1. Asegúrate de tener `django-cotton` instalado y configurado
2. Los componentes están en `templates/cotton/`
3. Usa `{% load cotton %}` en tus templates
4. Llama a los componentes con `{% c "nombre_componente" %}`

## Ejemplos de Implementación

Ver los templates refactorizados:
- `ciudadanos/ciudadano_list.html`
- `ciudadanos/ciudadano_confirm_delete.html`
- `comedor/comedor_list.html`

Para ejemplos completos de cómo implementar estos componentes en nuevos templates.