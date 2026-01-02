# Reporter de Provincias - Propuesta Técnica

## 📋 Descripción General

Pantalla de análisis gráfico para que las provincias puedan visualizar y analizar el estado de los casos que han subido, con enfoque en:
- Estados de validación en diferentes instancias
- Análisis de rechazos y aprobaciones
- Seguimiento de documentación
- Comentarios y observaciones
- Expedientes asociados

---

## 🎯 Funcionalidades Principales

### 1. **Filtros Avanzados**
- **Por Provincia**: Seleccionar una o todas
- **Rango de Fechas**: Desde/Hasta
- **Por Estado**: Pendiente, Aprobado, Rechazado
- **Botones**: Filtrar y Limpiar

### 2. **Estadísticas Generales (Cards)**
- Total de Casos
- Documentos Completos (con %)
- Documentos Incompletos (con %)
- Casos con Comentarios

### 3. **Instancias de Validación**

#### Validación Técnica
- Pendiente
- Aprobado ✓
- Rechazado ✗
- Subsanar ⚠
- Subsanado ✓

#### Cruce SINTYS
- Sin Cruce
- Match ✓
- No Match ✗

#### Estado de Cupo
- No Evaluado
- Dentro de Cupo ✓
- Fuera de Cupo ✗

### 4. **Gráficos Visuales**
- **Validación Técnica**: Gráfico de dona (doughnut)
- **Resultados SINTYS**: Gráfico de barras horizontal
- **Estado de Cupo**: Gráfico de pastel (pie)
- **Casos por Provincia**: Gráfico de barras horizontal

### 5. **Tabla de Detalle**
Últimos 50 casos con columnas:
- Documento
- Nombre
- Provincia
- Validación Técnica (badge)
- SINTYS (badge)
- Cupo (badge)
- Documentos (Completo/Incompleto)
- Fecha de creación

---

## 🏗️ Estructura Técnica

### Archivos Creados

#### 1. Vista: `celiaquia/views/reporter_provincias.py`
```python
class ReporterProvinciasView(LoginRequiredMixin, TemplateView)
```

**Responsabilidades:**
- Obtener parámetros de filtro (GET)
- Construir queryset con filtros
- Agregar datos por instancia
- Calcular estadísticas
- Preparar datos para gráficos

**Datos Agregados:**
- Conteos por estado de validación técnica
- Conteos por resultado SINTYS
- Conteos por estado de cupo
- Casos con documentos completos/incompletos
- Casos con comentarios
- Expedientes por provincia

#### 2. Template: `celiaquia/templates/celiaquia/reporter_provincias.html`
- Diseño responsive con CSS Grid
- Filtros en formulario GET
- Cards de estadísticas
- Secciones de instancias
- 4 gráficos con Chart.js
- Tabla de detalle con badges

#### 3. URL: `celiaquia/urls.py`
```python
path('reporter/provincias/', ReporterProvinciasView.as_view(), name='reporter_provincias')
```

**Permisos:** CoordinadorCeliaquia, TecnicoCeliaquia

---

## 📊 Datos Utilizados

### Modelos Consultados
- `ExpedienteCiudadano`: Datos principales de casos
- `Expediente`: Información de expedientes
- `Provincia`: Ubicación geográfica
- `HistorialComentarios`: Comentarios y observaciones

### Campos Utilizados
- `revision_tecnico`: Estado de validación técnica
- `resultado_sintys`: Resultado del cruce SINTYS
- `estado_cupo`: Estado de cupo
- `archivos_ok`: Documentación completa
- `creado_en`: Fecha de creación
- `ciudadano`: Datos del beneficiario
- `expediente__usuario_provincia__profile__provincia`: Provincia

---

## 🎨 Diseño Visual

### Paleta de Colores
- **Primario**: #667eea (Azul)
- **Éxito**: #10b981 (Verde)
- **Advertencia**: #f59e0b (Naranja)
- **Peligro**: #ef4444 (Rojo)
- **Info**: #3b82f6 (Azul claro)
- **Secundario**: #6b7280 (Gris)

### Componentes
- **Header**: Gradiente morado con título
- **Cards**: Blancas con borde izquierdo coloreado
- **Badges**: Pequeños con fondo y texto coloreado
- **Gráficos**: Chart.js con colores consistentes
- **Tabla**: Filas alternadas con hover

---

## 🔄 Flujo de Datos

```
GET /celiaquia/reporter/provincias/?provincia=1&fecha_desde=2024-01-01
    ↓
ReporterProvinciasView.get_context_data()
    ↓
Filtrar ExpedienteCiudadano
    ↓
Agregar por instancia (validación, SINTYS, cupo)
    ↓
Calcular estadísticas
    ↓
Preparar datos para gráficos
    ↓
Renderizar template con contexto
    ↓
HTML con gráficos Chart.js
```

---

## 📈 Ejemplos de Uso

### Caso 1: Ver todos los casos de una provincia
```
GET /celiaquia/reporter/provincias/?provincia=1
```
Muestra todos los casos de la provincia seleccionada.

### Caso 2: Filtrar por rango de fechas
```
GET /celiaquia/reporter/provincias/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31
```
Muestra casos dentro del rango especificado.

### Caso 3: Ver casos rechazados
```
GET /celiaquia/reporter/provincias/?estado=RECHAZADO
```
Muestra solo casos rechazados en validación técnica.

---

## 🔐 Seguridad

- **Autenticación**: LoginRequiredMixin
- **Autorización**: group_required(['CoordinadorCeliaquia', 'TecnicoCeliaquia'])
- **Filtrado**: Solo datos de expedientes del usuario
- **Inyección SQL**: Protegido por ORM de Django

---

## ⚡ Optimizaciones

### Queries Optimizadas
- `select_related()`: Expediente, Usuario, Provincia, Ciudadano
- `distinct()`: Para evitar duplicados en conteos
- Índices en BD: Ya existen en modelo

### Rendimiento
- Máximo 50 registros en tabla de detalle
- Agregaciones en BD (Count, annotate)
- Gráficos renderizados en cliente (Chart.js)

---

## 🚀 Próximas Mejoras

1. **Exportar a Excel**: Tabla de detalle
2. **Gráficos Temporales**: Evolución por mes
3. **Filtro por Técnico**: Asignaciones
4. **Drill-down**: Click en gráfico → detalle
5. **Comparativa**: Provincia vs Promedio
6. **Alertas**: Casos vencidos, pendientes críticos
7. **API**: Endpoint para datos en JSON

---

## 📝 Notas de Implementación

### Instalación
1. Crear archivo `celiaquia/views/reporter_provincias.py`
2. Crear template `celiaquia/templates/celiaquia/reporter_provincias.html`
3. Agregar URL en `celiaquia/urls.py`
4. No requiere migraciones

### Dependencias
- Django 3.2+
- Chart.js 4.4.0 (CDN)
- Bootstrap (ya incluido en base.html)

### Testing
```bash
# Acceder a la pantalla
http://localhost:8000/celiaquia/reporter/provincias/

# Con filtros
http://localhost:8000/celiaquia/reporter/provincias/?provincia=1&fecha_desde=2024-01-01
```

---

## 📞 Soporte

Para consultas sobre:
- **Datos**: Revisar modelos en `celiaquia/models.py`
- **Filtros**: Modificar `get_context_data()` en vista
- **Diseño**: Editar CSS en template
- **Gráficos**: Configurar Chart.js en bloque `extra_js`
