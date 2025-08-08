// custom/js/centrodefamilia.js

document.addEventListener("DOMContentLoaded", function() {
  // 1) FILTRO EN VIVO DE CENTROS ADHERIDOS
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

  // 3) FILTRO POR QUERY STRING PARA ACTIVIDADES
  updateQueryParam("searchActividades", "search_actividades");
  updateQueryParam("searchCurso", "search_actividades_curso");
});

// Función para actualizar parámetros en la URL y recargar
function updateQueryParam(inputId, paramName) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.addEventListener('input', function () {
    const url = new URL(window.location);
    const value = this.value;
    url.searchParams.set(paramName, value);
    if (paramName === "search_actividades") {
      url.searchParams.delete("page_act");
    } else if (paramName === "search_actividades_curso") {
      url.searchParams.delete("page");
    }
    window.location = url.toString();
  });
}
