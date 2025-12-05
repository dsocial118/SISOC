/**
 * Ordenamiento de tabla de comedores
 * Permite ordenar la tabla por columnas con clicks en los headers
 */

document.addEventListener("DOMContentLoaded", function () {
  const table = document.querySelector(".table-comedor-moderno");
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

    // Obtener todas las filas (excluyendo la fila "empty")
    const rows = Array.from(tbody.querySelectorAll("tr")).filter((row) => {
      return !row.querySelector(".no-comedores-message");
    });

    // Ordenar las filas
    rows.sort((a, b) => {
      let aValue, bValue;

      if (column === "nombre") {
        aValue = a.querySelector('td[data-nombre]')?.getAttribute("data-nombre") || "";
        bValue = b.querySelector('td[data-nombre]')?.getAttribute("data-nombre") || "";

        // Normalizar para comparación (minúsculas, sin acentos)
        aValue = aValue.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        bValue = bValue.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      } else if (column === "validacion") {
        aValue = a.querySelector('td[data-validacion]')?.getAttribute("data-validacion") || "";
        bValue = b.querySelector('td[data-validacion]')?.getAttribute("data-validacion") || "";

        // Orden de prioridad: Validado > Pendiente > No Validado
        const priority = {
          "Validado": 3,
          "Pendiente": 2,
          "No Validado": 1,
          "": 0
        };

        aValue = priority[aValue] || 0;
        bValue = priority[bValue] || 0;
      }

      // Comparar valores
      let comparison = 0;
      if (typeof aValue === "string") {
        comparison = aValue.localeCompare(bValue, "es", { sensitivity: "base" });
      } else {
        comparison = aValue - bValue;
      }

      // Aplicar dirección
      return direction === "asc" ? comparison : -comparison;
    });

    // Limpiar tbody y agregar filas ordenadas
    tbody.innerHTML = "";
    rows.forEach((row) => tbody.appendChild(row));

    // Si había una fila "empty", agregarla de nuevo al final
    const emptyRow = Array.from(tbody.querySelectorAll("tr")).find((row) =>
      row.querySelector(".no-comedores-message")
    );
    if (emptyRow) {
      tbody.appendChild(emptyRow);
    }

    // Agregar animación de fade in
    rows.forEach((row, index) => {
      row.style.animation = "none";
      setTimeout(() => {
        row.style.animation = "";
      }, index * 20);
    });
  }
});
