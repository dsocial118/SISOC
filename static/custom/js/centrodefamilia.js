// centrodefamilia.js

document.addEventListener("DOMContentLoaded", function() {
  // 1) FILTROS EN VIVO

  // Filtrar Centros
  const filtroCentros = document.getElementById('filterCentros');
  const tablaCentros = document.querySelector('#tablaCentros tbody');
  if (filtroCentros && tablaCentros) {
    filtroCentros.addEventListener('input', () => {
      const termino = filtroCentros.value.trim().toLowerCase();
      tablaCentros.querySelectorAll('tr').forEach(fila => {
        const nombre = fila.cells[0].textContent.trim().toLowerCase();
        fila.style.display = nombre.startsWith(termino) ? '' : 'none';
      });
    });
  }

  // Filtrar Actividades (por Centro, Actividad, Categoría, Estado)
  const filtroActividades = document.getElementById('filterActividades');
  const tablaActividades = document.querySelector('#tablaActividades tbody');
  if (filtroActividades && tablaActividades) {
    filtroActividades.addEventListener('input', () => {
      const termino = filtroActividades.value.trim().toLowerCase();
      tablaActividades.querySelectorAll('tr').forEach(fila => {
        const textos = Array.from(fila.cells)
          .slice(0, 4)
          .map(celda => celda.textContent.trim().toLowerCase());
        const coincide = textos.some(texto => texto.startsWith(termino));
        fila.style.display = coincide ? '' : 'none';
      });
    });
  }

  // 2) AJAX PARA PAGINACIÓN DE INFORMES CABAL
  document.addEventListener('click', function(evento) {
    const enlace = evento.target.closest('#expedientes-container .pagination a');
    if (!enlace) return;
    evento.preventDefault();
    fetch(enlace.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(respuesta => respuesta.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const nuevoContenedor = doc.querySelector('#expedientes-container');
        if (nuevoContenedor) {
          document.querySelector('#expedientes-container').innerHTML =
            nuevoContenedor.innerHTML;
        }
      });
  });

  // Filtrar Expedientes
  const buscadorExpedientes = document.getElementById('searchExpedientes');
  const tablaExpedientes = document.querySelector('#tablaExpedientes tbody');
  if (buscadorExpedientes && tablaExpedientes) {
    buscadorExpedientes.addEventListener('input', () => {
      const termino = buscadorExpedientes.value.trim().toLowerCase();
      tablaExpedientes.querySelectorAll('tr').forEach(fila => {
        const archivo = fila.cells[0].textContent.trim().toLowerCase();
        const periodo = fila.cells[1].textContent.trim().toLowerCase();
        fila.style.display = (archivo.includes(termino) || periodo.includes(termino))
          ? '' 
          : 'none';
      });
    });
  }
});
