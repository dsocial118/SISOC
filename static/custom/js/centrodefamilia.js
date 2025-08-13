document.addEventListener("DOMContentLoaded", function () {

  /* ==========================================================
     1) ANIMACIÓN DE PESTAÑAS LATERALES Y SECCIONES
  ========================================================== */

  // ---- ACCORDION LATERAL ----
  function ajustarAnchos() {
    const allPanels = document.querySelectorAll('.accordion-panel');
    const totalPanels = allPanels.length;
    const closedWidth = 60; // ancho cerrado

    const openPanel = Array.from(allPanels).find(p => p.classList.contains('open'));

    if (!openPanel) {
        // Si ninguno está abierto, todos cerrados
        allPanels.forEach(p => p.style.width = closedWidth + 'px');
        return;
    }

    const openWidth = `calc(100% - ${(totalPanels - 1) * closedWidth}px)`;

    allPanels.forEach(p => {
        if (p === openPanel) {
            p.style.width = openWidth;
        } else {
            p.style.width = closedWidth + 'px';
        }
    });
  }

  function toggleAccordion(panel) {
    const allPanels = document.querySelectorAll('.accordion-panel');
    const totalPanels = allPanels.length;
    const closedWidth = 60; // px

    if (panel.classList.contains('open')) {
        panel.classList.remove('open');
        allPanels.forEach(p => p.style.width = closedWidth + 'px');
        return;
    }

    // Cerrar todos
    allPanels.forEach(p => p.classList.remove('open'));

    // Abrir el seleccionado
    panel.classList.add('open');

    const openWidth = `calc(100% - ${(totalPanels - 1) * closedWidth}px)`;

    allPanels.forEach(p => {
        p.style.width = p.classList.contains('open') ? openWidth : closedWidth + 'px';
    });
  }

  // Ejecutar al cargar
  ajustarAnchos();

  // Asignar click a cada panel
  document.querySelectorAll('.accordion-panel').forEach(panel => {
    panel.addEventListener('click', () => toggleAccordion(panel));
  });

  /* ==========================================================
     2) FILTRO EN VIVO DE CENTROS ADHERIDOS
  ========================================================== */
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

  /* ==========================================================
     3) AJAX PARA PAGINACIÓN DE INFORMES CABAL
  ========================================================== */
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

  /* ==========================================================
     4) FILTROS POR QUERY STRING PARA ACTIVIDADES
  ========================================================== */
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
  updateQueryParam("searchActividades", "search_actividades");
  updateQueryParam("searchCurso", "search_actividades_curso");

});
