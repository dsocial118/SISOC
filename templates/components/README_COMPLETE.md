# 📦 Biblioteca Completa de Componentes - SISOC Backoffice

Esta carpeta contiene una **biblioteca completa de 14 componentes** reutilizables usando `{% include %}` de Django.

## ✅ Ventajas de esta implementación

🚀 **Sin dependencias externas** - Solo Django vanilla  
🎯 **Reutilización completa** - Un solo lugar para cada patrón de UI  
🔧 **Mantenimiento fácil** - Cambios globales desde un archivo  
⚡ **Performance optimizada** - Sin overhead adicional  
🐛 **Debugging simple** - Errores de template claros  
🎨 **Fácil personalización** - CSS y clases modificables  

---

## 📦 Catálogo Completo de Componentes

### 🧭 **Componentes de Navegación**

#### 1. `breadcrumb.html` - Migas de Pan
```django
{% include 'components/breadcrumb.html' with items=breadcrumb_items %}
```

#### 2. `search_bar.html` - Barra de Búsqueda
```django
{% include 'components/search_bar.html' with titulo="Buscar Items" placeholder="Buscar..." reset_url=reset_url add_url=add_url %}
```

#### 3. `pagination.html` - Paginación
```django
{% include 'components/pagination.html' with is_paginated=is_paginated page_obj=page_obj %}
```

### 📊 **Componentes de Datos**

#### 4. `data_table.html` - Tabla Completa con Acciones
```django
{% include 'components/data_table.html' with headers=headers items=object_list show_actions=True %}
```

#### 5. `stats_card.html` - Tarjetas de Estadísticas
```django
{% include 'components/stats_card.html' with title="Usuarios" value="150" icon="fas fa-users" color="primary" %}
```

#### 6. `info_card.html` - Tarjetas de Información
```django
{% include 'components/info_card.html' with title="Datos" list_style=True items=data_items %}
```

#### 7. `timeline.html` - Línea de Tiempo
```django
{% include 'components/timeline.html' with events=timeline_events %}
```

### 📝 **Componentes de Formularios**

#### 8. `form_field.html` - Campos de Formulario
```django
{% include 'components/form_field.html' with field=form.nombre label="Nombre completo" %}
```

#### 9. `form_stepper.html` - Stepper de Formularios
```django
{% include 'components/form_stepper.html' with steps=stepper_steps current_step=1 %}
```

#### 10. `form_buttons.html` - Botones de Formulario
```django
{% include 'components/form_buttons.html' with cancel_url=cancel_url buttons=form_buttons %}
```

### 🎯 **Componentes de Interacción**

#### 11. `action_buttons.html` - Botones de Acción
```django
{% include 'components/action_buttons.html' with back_button=back_btn buttons=action_buttons %}
```

#### 12. `modal.html` - Modales
```django
{% include 'components/modal.html' with modal_id="myModal" title="Mi Modal" content="Contenido..." %}
```

#### 13. `tabs.html` - Pestañas
```django
{% include 'components/tabs.html' with tabs=tab_items active_tab="tab1" %}
```

### 💬 **Componentes de Feedback**

#### 14. `alert_message.html` - Mensajes de Alerta
```django
{% include 'components/alert_message.html' with type="success" message="Operación exitosa" %}
```

### 🎨 **Componentes Auxiliares**

#### 15. `loading_spinner.html` - Indicadores de Carga
```django
{% include 'components/loading_spinner.html' with type="border" color="primary" %}
```

#### 16. `empty_state.html` - Estados Vacíos
```django
{% include 'components/empty_state.html' with icon="fas fa-inbox" title="No hay datos" %}
```

#### 17. `delete_confirm.html` - Confirmación de Eliminación
```django
{% include 'components/delete_confirm.html' with object_name=object cancel_url=cancel_url %}
```

---

## 🎯 Ejemplos de Uso Prácticos

### Template Lista Completo
```django
{% extends "includes/main.html" %}
{% load static %}

{% block breadcrumb %}
    {% include 'components/breadcrumb.html' with items=breadcrumb_items %}
{% endblock %}

{% block content %}
    <!-- Mensajes del sistema -->
    {% include 'components/alert_message.html' with show_django_messages=True %}
    
    <!-- Barra de búsqueda -->
    {% include 'components/search_bar.html' with titulo="Buscar Ciudadanos" reset_url=reset_url add_url=add_url %}
    
    <!-- Tabla de datos con paginación integrada -->
    {% include 'components/data_table.html' with headers=headers items=object_list show_actions=True include_pagination=True %}
{% endblock %}
```

### Dashboard con Estadísticas
```django
{% block content %}
    <div class="row">
        {% include 'components/stats_card.html' with title="Total Usuarios" value=total_users icon="fas fa-users" color="primary" col_class="col-md-3" %}
        {% include 'components/stats_card.html' with title="Nuevos Hoy" value=new_today icon="fas fa-user-plus" color="success" col_class="col-md-3" %}
        {% include 'components/stats_card.html' with title="Pendientes" value=pending icon="fas fa-clock" color="warning" col_class="col-md-3" %}
        {% include 'components/stats_card.html' with title="Completados" value=completed icon="fas fa-check" color="info" col_class="col-md-3" %}
    </div>
{% endblock %}
```

### Formulario Multi-Paso
```django
{% block content %}
    {% include 'components/form_stepper.html' with steps=stepper_steps current_step=current_step %}
    
    <form method="POST">
        {% csrf_token %}
        <div class="row">
            {% include 'components/form_field.html' with field=form.nombre col_class="col-md-6" %}
            {% include 'components/form_field.html' with field=form.email col_class="col-md-6" field_type="email" %}
        </div>
        
        {% include 'components/form_buttons.html' with cancel_url=cancel_url default_save=True default_continue=True %}
    </form>
{% endblock %}
```

---

## 🔧 Preparación de Vistas

```python
class MiListView(ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Breadcrumb
        context['breadcrumb_items'] = [
            {"text": "Dashboard", "url": reverse("dashboard")},
            {"text": "Mi Sección", "active": True}
        ]
        
        # Search bar
        context['reset_url'] = reverse("mi_lista")
        context['add_url'] = reverse("mi_crear")
        context['query'] = self.request.GET.get("busqueda")
        
        # Data table
        context['headers'] = [
            {"title": "Nombre"},
            {"title": "Email"}, 
            {"title": "Estado"}
        ]
        
        # Stats cards
        context['total_users'] = Usuario.objects.count()
        context['new_today'] = Usuario.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
        
        return context
```

---

## 🎨 Personalización Global

### Cambiar Colores de Toda la Aplicación
```python
# En tu vista o context processor
BRAND_COLORS = {
    'primary': 'indigo',
    'success': 'emerald', 
    'danger': 'red',
    'warning': 'yellow'
}
```

### Estilos CSS Personalizados
```css
/* custom.css */
.stats-card {
    transition: transform 0.2s;
}
.stats-card:hover {
    transform: translateY(-4px);
}
```

---

## 📋 Checklist de Implementación

### Para nuevos templates:
- [ ] ✅ Usar `breadcrumb.html` en vez de HTML manual
- [ ] ✅ Usar `search_bar.html` para búsquedas  
- [ ] ✅ Usar `data_table.html` para tablas
- [ ] ✅ Usar `pagination.html` para paginación
- [ ] ✅ Usar `alert_message.html` para mensajes
- [ ] ✅ Usar `delete_confirm.html` para eliminaciones

### Para refactorizar templates existentes:
- [ ] ✅ Identificar patrones repetitivos
- [ ] ✅ Preparar datos en la vista
- [ ] ✅ Reemplazar HTML por includes
- [ ] ✅ Probar funcionamiento
- [ ] ✅ Actualizar CSS si es necesario

---

## 🎯 Resultado Final

Con estos **17 componentes**, tienes todo lo necesario para:

✅ **Listas paginadas** consistentes  
✅ **Formularios multi-paso** estandarizados  
✅ **Dashboards con estadísticas** uniformes  
✅ **Confirmaciones de eliminación** coherentes  
✅ **Modales y alertas** reutilizables  
✅ **Estados vacíos** informativos  
✅ **Timeline de actividades** elegantes  

**¡Tu aplicación tendrá un diseño completamente consistente y será súper fácil de mantener!** 🚀
