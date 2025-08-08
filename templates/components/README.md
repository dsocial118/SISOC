# Componentes Reutilizables - SISOC Backoffice

Esta carpeta contiene una **biblioteca completa** de componentes reutilizables usando `{% include %}` de Django para el proyecto SISOC-Backoffice.

## Ventajas de este enfoque

✅ **Simplicidad**: No requiere librerías adicionales  
✅ **Reutilización**: Código HTML componentizado  
✅ **Mantenimiento**: Fácil de actualizar diseños  
✅ **Flexibilidad**: Compatible con cualquier versión de Django  
✅ **Debugging**: Errores más claros que Cotton  
✅ **Performance**: Sin overhead adicional

## 📦 Colección Completa de Componentes (14 componentes)

### 🧭 Componentes de Navegación

### 1. `breadcrumb.html` - Migas de Pan

**Uso:**
```django
{% include 'components/breadcrumb.html' with items=breadcrumb_items class='extra-class' %}
```

**Datos esperados en la vista:**
```python
context['breadcrumb_items'] = [
    {"text": "Inicio", "url": reverse("home")},
    {"text": "Sección", "url": reverse("seccion")},
    {"text": "Página Actual", "active": True}
]
```

### 2. `search_bar.html` - Barra de Búsqueda

**Uso básico:**
```django
{% include 'components/search_bar.html' with titulo="Buscar Items" placeholder="Ingrese búsqueda" reset_url=reset_url add_url=add_url %}
```

**Uso completo:**
```django
{% include 'components/search_bar.html' with titulo="Buscar Ciudadano" placeholder="Buscar DNI o apellido" help_text="Ingrese términos de búsqueda" reset_url=reset_url add_url=add_url show_add_button=can_add query=query add_text="Agregar Nuevo" button_append=True %}
```

**Parámetros disponibles:**
- `titulo` (opcional): Título de la sección. Default: "Buscar"
- `placeholder` (opcional): Placeholder del input. Default: "Buscar"  
- `help_text` (opcional): Tooltip del input. Default: "Ingrese términos de búsqueda"
- `reset_url`: URL para botón "Resetear"
- `add_url` (opcional): URL para botón "Agregar"
- `show_add_button` (opcional): Mostrar botón agregar. Default: True
- `query` (opcional): Valor actual de búsqueda
- `add_text` (opcional): Texto botón agregar. Default: "Agregar"
- `button_append` (opcional): Usar input-group-append. Default: False

### 3. `pagination.html` - Paginación

**Uso:**
```django
{% include 'components/pagination.html' with is_paginated=is_paginated page_obj=page_obj page_range=page_range query=query %}
```

**Parámetros:**
- `is_paginated`: Boolean de Django ListView
- `page_obj`: Objeto page de Django
- `page_range` (opcional): Rango personalizado de páginas
- `query` (opcional): Query de búsqueda para mantener en URLs
- `prev_text` (opcional): Texto botón anterior. Default: "Volver"
- `next_text` (opcional): Texto botón siguiente. Default: "Continuar"

### 4. `delete_confirm.html` - Confirmación de Eliminación

**Uso:**
```django
{% include 'components/delete_confirm.html' with object_name=object warning_items=relaciones_existentes cancel_url=cancel_url %}
```

**Parámetros:**
- `object_name`: Nombre del objeto a eliminar
- `title` (opcional): Título personalizado. Default: "Atención!"
- `message` (opcional): Mensaje personalizado
- `warning_items` (opcional): Lista de advertencias/relaciones
- `warning_message` (opcional): Mensaje de advertencia personalizado
- `cancel_url`: URL para cancelar
- `confirm_text` (opcional): Texto botón confirmar. Default: "Eliminar"
- `cancel_text` (opcional): Texto botón cancelar. Default: "Cancelar"

### 5. `action_buttons.html` - Botones de Acción

**Uso:**
```django
{% include 'components/action_buttons.html' with back_button=back_btn buttons=action_buttons %}
```

**Estructura de datos:**
```python
back_button = {
    "url": reverse("lista"),
    "text": "Volver", 
    "type": "outline-light",  # opcional
    "icon": "fas fa-arrow-left"  # opcional
}

buttons = [
    {
        "url": reverse("editar", kwargs={"pk": obj.id}),
        "text": "Editar",
        "type": "primary",
        "icon": "fas fa-edit",  # opcional
        "permission": True,  # opcional
        "class": "custom-class"  # opcional
    }
]
```

### 6. `info_card.html` - Tarjeta de Información

**Uso estilo lista:**
```django
{% include 'components/info_card.html' with title="Datos Personales" list_style=True items=data_items %}
```

**Uso estilo icono + valor:**
```django
{% include 'components/info_card.html' with title="Estadísticas" icon_value_style=True icon="fas fa-users" value="150" link_url=detail_url link_text="Ver más" %}
```

**Estructura de datos para lista:**
```python
data_items = [
    {"label": "Nombre", "value": ciudadano.nombre},
    {"label": "DNI", "value": ciudadano.documento},
    {"label": "Email", "value": ciudadano.email or "–"}
]
```

## Preparación de las Vistas

Para usar estos componentes, las vistas deben preparar los datos:

```python
class MiListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            # Breadcrumb
            "breadcrumb_items": [
                {"text": "Inicio", "url": reverse("home")},
                {"text": "Mi Sección", "active": True}
            ],
            # Search bar
            "reset_url": reverse("mi_lista"),
            "add_url": reverse("mi_crear"),
            "can_add": self.request.user.has_perm('mi_app.add_modelo'),
            "query": self.request.GET.get("busqueda"),
            # Action buttons
            "back_button": {
                "url": reverse("dashboard"),
                "text": "Volver al Dashboard",
                "icon": "fas fa-home"
            }
        })
        return context
```

## Ejemplos de Implementación

### Template Lista Completo
```django
{% extends "includes/main.html" %}
{% load static %}

{% block breadcrumb %}
    {% include 'components/breadcrumb.html' with items=breadcrumb_items %}
{% endblock %}

{% block content %}
    {% include 'components/search_bar.html' with titulo="Buscar Items" placeholder="Buscar..." reset_url=reset_url add_url=add_url %}
    
    <div class="row mt-5">
        <div class="col-12">
            <div class="card">
                <div class="card-body">
                    <!-- Tu tabla aquí -->
                    {% include 'components/pagination.html' with is_paginated=is_paginated page_obj=page_obj query=query %}
                </div>
            </div>
        </div>
    </div>
{% endblock %}
```

### Template Delete Completo
```django
{% extends "includes/main.html" %}
{% load static %}

{% block breadcrumb %}
    {% include 'components/breadcrumb.html' with items=breadcrumb_items %}
{% endblock %}

{% block content %}
    {% include 'components/delete_confirm.html' with object_name=object warning_items=relaciones_existentes cancel_url=cancel_url %}
{% endblock %}
```

## Personalización

Los componentes pueden personalizarse pasando clases CSS adicionales:

```django
{% include 'components/info_card.html' with title="Mi Card" card_class="border-primary" header_class="bg-primary text-white" %}
```

## Migración desde Cotton

Si tienes componentes Cotton existentes, simplemente reemplaza:

```django
<!-- ANTES (Cotton) -->
{% load cotton %}
{% c "breadcrumb" items=breadcrumb_items %}

<!-- DESPUÉS (Include) -->
{% include 'components/breadcrumb.html' with items=breadcrumb_items %}
```

## Ventajas vs Cotton

1. **Sin dependencias externas** - Solo Django vanilla
2. **Más fácil debugging** - Errores de template más claros
3. **Mejor performance** - Sin procesamiento adicional
4. **Compatible con cualquier versión** - No depende de versiones específicas
5. **Más flexible** - Fácil de personalizar y extender