# Análisis: transición del código de proyecto desde comedor hacia la organización

**Fecha:** 2026-07-22  
**Contexto:** hoy el campo "Código de Proyecto" está en el modelo de comedor, pero el negocio requiere que ese dato pertenezca a la organización y que, al seleccionar una organización en el legajo de un comedor, se puedan elegir únicamente los proyectos válidos para esa organización.

---

## 1. Problema actual

Actualmente el campo `codigo_de_proyecto` vive en el modelo de comedor y se completa al dar de alta o editar un comedor.

Eso genera dos problemas operativos:

1. la organización no tiene un registro explícito de los proyectos con los que trabaja;
2. el dato queda duplicado y depende del legajo del comedor, cuando el concepto de proyecto debería estar asociado a la organización como entidad de negocio.

---

## 2. Objetivo de la transición

Mover el concepto de proyecto a un nivel superior, de modo que:

- la organización administre los proyectos con los que puede operar;
- el comedor seleccione un proyecto válido para la organización elegida;
- la información histórica se conserve sin romper el flujo existente.

---

## 3. Propuesta recomendada

### Recomendación principal

La mejor propuesta no es solo agregar un campo `codigo_de_proyecto` a la organización, porque eso no resuelve bien el requisito de "diferentes proyectos por organización".

La propuesta más robusta es modelar los proyectos como una entidad propia relacionada con la organización.

### Modelo sugerido

Crear una entidad nueva, por ejemplo:

- `ProyectoOrganizacion` (o `Proyecto` si el nombre encaja mejor en el dominio)

Campos sugeridos:

- `organizacion`: FK a `Organizacion`
- `codigo`: código del proyecto
- `nombre`: nombre legible del proyecto (opcional)
- `activo`: para desactivar proyectos sin borrar datos
- `es_default`: para marcar un proyecto por defecto cuando corresponda

### Relación con comedor

El modelo de comedor debería pasar a usar una relación al proyecto, por ejemplo:

- `proyecto`: FK a `ProyectoOrganizacion`

De esta forma:

- una organización puede tener muchos proyectos;
- un comedor solo puede elegir entre los proyectos de la organización seleccionada;
- la lógica queda alineada con el negocio y con la necesidad de escalar.

---

## 4. Por qué esta propuesta es mejor que solo agregar un campo a organización

Agregar un único campo en `Organizacion` sería una solución mínima, pero tiene limitaciones claras:

- no permite representar múltiples proyectos por organización;
- obliga a reutilizar un único valor y complica el mantenimiento futuro;
- no escala bien si una organización participa en varias líneas de proyecto.

La propuesta de entidad propia resuelve el problema de forma limpia y evita volver a refactorizar más adelante.

---

## 5. Plan de transición recomendado

### Fase 1 - Preparación y migración de datos

Objetivo: conservar la información actual sin romper el funcionamiento.

Acciones:

1. agregar la nueva entidad de proyectos vinculada a la organización;
2. cargar los datos actuales desde `Comedor.codigo_de_proyecto` y crear un registro por cada combinación distinta de organización + código de proyecto;
3. dejar el campo actual en el comedor como dato de compatibilidad temporal.

### Fase 2 - Integración en el flujo de alta/edición de comedor

Objetivo: que el usuario elija correctamente el proyecto según la organización.

Acciones:

1. en el formulario de comedor, filtrar los proyectos disponibles según la organización seleccionada;
2. si la organización ya tiene proyectos, mostrar solo esos valores;
3. si no tiene proyectos, mostrar una advertencia clara o bloquear la selección hasta cargar el proyecto correspondiente.

### Fase 3 - Migración del uso del dato en backend y APIs

Objetivo: reemplazar el uso del campo directo de comedor por la relación con proyecto.

Acciones:

1. ajustar serializers y vistas para exponer el proyecto asociado;
2. actualizar reglas de negocio y filtros;
3. conservar compatibilidad para lectura de los datos viejos durante la transición.

### Fase 4 - Limpieza y consolidación

Objetivo: dejar el modelo en su estado final.

Acciones:

1. migrar las pantallas y reportes para usar la nueva relación;
2. eliminar el campo heredado `codigo_de_proyecto` del comedor cuando no quede consumo activo;
3. dejar una regla de migración y documentación para futuros datos.

---

## 6. Compatibilidad con la implementación actual

Para no romper el sistema de una vez, la transición puede hacerse en modo gradual:

- mantener temporalmente `codigo_de_proyecto` en `Comedor`;
- usar la nueva relación de proyecto como fuente de verdad nueva;
- sincronizar ambos valores durante la migración inicial;
- luego quitar el campo heredado cuando todo el flujo esté migrado.

Esto reduce el riesgo y permite validar el cambio sin una ruptura completa.

---

## 7. Reglas de negocio sugeridas

Para evitar ambigüedades, conviene definir reglas claras:

- un comedor debe tener un proyecto asociado;
- ese proyecto debe pertenecer a la organización del comedor;
- si la organización cambia, el proyecto debe volver a validarse;
- si una organización no tiene proyectos cargados, el alta debería advertirlo.

---

## 8. Criterios de aceptación

La tarea se considera cumplida cuando:

1. una organización puede tener múltiples proyectos asociados;
2. un comedor solo puede elegir proyectos válidos para su organización;
3. los datos actuales se migran correctamente desde el estado anterior;
4. la UI, la API y el backend usan la nueva relación de forma consistente;
5. no se pierde trazabilidad histórica de los códigos de proyecto ya existentes.

---

## 9. Tarea propuesta para implementar

### Título

Migración del código de proyecto desde comedor hacia la organización como entidad de proyectos por organización.

### Alcance

- definir y crear la nueva entidad de proyectos asociados a organización;
- migrar los datos existentes desde los comedores;
- ajustar formularios, vistas y APIs para usar la nueva relación;
- dejar una transición segura y documentada.

### Entregables

- modelo nuevo para proyectos por organización;
- migración de datos inicial;
- adaptación del alta/edición de comedor;
- adaptación de serializers y vistas;
- documentación operativa de la transición.

---

## 10. Recomendación final

La mejor propuesta es adoptar una relación de uno a muchos entre organización y proyectos, y mover la selección del proyecto al legajo del comedor como un valor dependiente de la organización.

Esto es más limpio, más escalable y más alineado con la necesidad de trabajar con múltiples proyectos por organización, sin perder compatibilidad con el estado actual.
