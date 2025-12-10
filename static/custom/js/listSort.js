/**
 * Ordenamiento genérico de tablas
 * Permite ordenar cualquier tabla con headers .sortable por columnas con clicks
 * Reutilizable para todos los listados
 */

document.addEventListener("DOMContentLoaded", function () {
  // Buscar tabla - priorizar .table-comedor-moderno, luego .table, luego .projects
  const table = document.querySelector(".table-comedor-moderno, .table, .projects");
  if (!table) return;

  const tbody = table.querySelector("tbody");
  const sortableHeaders = table.querySelectorAll("thead th.sortable");

  // Estado del ordenamiento: {column: 'nombre', direction: 'asc' | 'desc'}
  let currentSort = {
    column: null,
    direction: null,
  };

  sortableHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const column = this.getAttribute("data-column");

      // Determinar dirección del ordenamiento
      if (currentSort.column === column) {
        // Si es la misma columna, alternar dirección
        if (currentSort.direction === "asc") {
          currentSort.direction = "desc";
        } else if (currentSort.direction === "desc") {
          // Si ya está descendente, quitar ordenamiento
          currentSort.column = null;
          currentSort.direction = null;
        } else {
          currentSort.direction = "asc";
        }
      } else {
        // Nueva columna, empezar con ascendente
        currentSort.column = column;
        currentSort.direction = "asc";
      }

      // Actualizar iconos de todos los headers
      updateHeaderIcons();

      // Ordenar la tabla
      sortTable(column, currentSort.direction);
    });
  });

  function updateHeaderIcons() {
    sortableHeaders.forEach((header) => {
      const column = header.getAttribute("data-column");
      const icon = header.querySelector(".sort-icon");

      // Remover clases de ordenamiento
      header.classList.remove("sort-asc", "sort-desc");

      if (currentSort.column === column) {
        if (currentSort.direction === "asc") {
          icon.classList.remove("fa-sort", "fa-sort-down");
          icon.classList.add("fa-sort-up");
          header.classList.add("sort-asc");
        } else if (currentSort.direction === "desc") {
          icon.classList.remove("fa-sort", "fa-sort-up");
          icon.classList.add("fa-sort-down");
          header.classList.add("sort-desc");
        }
      } else {
        icon.classList.remove("fa-sort-up", "fa-sort-down");
        icon.classList.add("fa-sort");
      }
    });
  }

  function sortTable(column, direction) {
    // Si no hay dirección, restaurar orden original
    if (!direction) {
      // No hay una forma fácil de restaurar el orden original sin guardarlo
      // Por ahora, simplemente no hacemos nada
      return;
    }

    // Obtener todas las filas (excluyendo filas de mensajes vacíos)
    const rows = Array.from(tbody.querySelectorAll("tr")).filter((row) => {
      return !row.querySelector(".no-comedores-message, .no-data-message, .empty-message") &&
             !row.querySelector('td[colspan]');
    });

    // Ordenar las filas
    rows.sort((a, b) => {
      let aValue, bValue;

      // Buscar la celda con el atributo data-{column}
      const dataAttr = `data-${column}`;
      aValue = a.querySelector(`td[${dataAttr}]`)?.getAttribute(dataAttr) || "";
      bValue = b.querySelector(`td[${dataAttr}]`)?.getAttribute(dataAttr) || "";

      // Si no hay atributo data-*, intentar obtener el texto de la celda
      if (aValue === "" && bValue === "") {
        const headerIndex = Array.from(sortableHeaders).findIndex(
          h => h.getAttribute("data-column") === column
        );
        if (headerIndex !== -1) {
          aValue = a.querySelectorAll("td")[headerIndex]?.textContent.trim() || "";
          bValue = b.querySelectorAll("td")[headerIndex]?.textContent.trim() || "";
        }
      }

      // Detectar tipo de valor
      let isNumber = false;
      let aNum = parseFloat(aValue);
      let bNum = parseFloat(bValue);

      if (!isNaN(aNum) && !isNaN(bNum) && aValue !== "" && bValue !== "") {
        isNumber = true;
      }

      // Normalizar strings para comparación (minúsculas, sin acentos)
      if (!isNumber) {
        // Manejar casos especiales de validación
        if (column === "validacion") {
          const priority = {
            "Validado": 3,
            "Pendiente": 2,
            "No Validado": 1,
            "": 0
          };
          aNum = priority[aValue] || 0;
          bNum = priority[bValue] || 0;
          isNumber = true;
        } else {
          aValue = aValue.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
          bValue = bValue.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        }
      }

      // Comparar valores
      let comparison = 0;
      if (isNumber) {
        comparison = aNum - bNum;
      } else {
        comparison = aValue.localeCompare(bValue, "es", { sensitivity: "base" });
      }

      // Aplicar dirección
      return direction === "asc" ? comparison : -comparison;
    });

    // Limpiar tbody y agregar filas ordenadas
    tbody.innerHTML = "";
    rows.forEach((row) => tbody.appendChild(row));

    // Si había una fila "empty", agregarla de nuevo al final
    const emptyRows = Array.from(tbody.querySelectorAll("tr")).filter((row) =>
      row.querySelector(".no-comedores-message, .no-data-message, .empty-message") ||
      row.querySelector('td[colspan]')
    );
    emptyRows.forEach((row) => tbody.appendChild(row));

    // Agregar animación de fade in
    rows.forEach((row, index) => {
      row.style.animation = "none";
      setTimeout(() => {
        row.style.animation = "";
      }, index * 20);
    });
  }
});
