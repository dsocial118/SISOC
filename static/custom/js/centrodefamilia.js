// centrodefamilia.js

document.addEventListener("DOMContentLoaded", function() {
  //
  // 1) FILTROS EN VIVO
  //
  // Filtrar Centros
  const fc = document.getElementById('filterCentros');
  const tbC = document.querySelector('#tablaCentros tbody');
  if (fc && tbC) {
    fc.addEventListener('input', () => {
      const term = fc.value.trim().toLowerCase();
      tbC.querySelectorAll('tr').forEach(row => {
        const nombre = row.cells[0].textContent.trim().toLowerCase();
        row.style.display = nombre.startsWith(term) ? '' : 'none';
      });
    });
  }

  // Filtrar Actividades (por Centro, Actividad, Categoría, Estado)
  const fa = document.getElementById('filterActividades');
  const tbA = document.querySelector('#tablaActividades tbody');
  if (fa && tbA) {
    fa.addEventListener('input', () => {
      const term = fa.value.trim().toLowerCase();
      tbA.querySelectorAll('tr').forEach(row => {
        // recorre las cuatro columnas relevantes
        const texts = Array.from(row.cells)
          .slice(0, 4)
          .map(cell => cell.textContent.trim().toLowerCase());
        const matches = texts.some(text => text.startsWith(term));
        row.style.display = matches ? '' : 'none';
      });
    });
  }
});
