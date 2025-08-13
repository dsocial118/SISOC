document.addEventListener("DOMContentLoaded", function () {

  /* ==========================================================
     1) ANIMACIÓN DE PESTAÑAS LATERALES Y SECCIONES
  ========================================================== */
  const locCard     = document.querySelector('.location-card');
  const leftTab     = document.getElementById('tab-ubicacion');
  const rightTabs   = locCard.querySelector('.right-tabs');
  const tabs        = Array.from(rightTabs.children);
  const mapCont     = document.getElementById('mapa-iframe');
  const detailsCont = document.getElementById('detalles-ubicacion');
  const sections    = Array.from(locCard.querySelectorAll('.content-seccion'));

  // Aumentar tamaño del mapa/detalles un 25%
  if (mapCont) mapCont.style.height = "125%";
  if (detailsCont) detailsCont.style.height = "125%";

  // Transición más suave para movimiento
  tabs.forEach(t => {
    t.style.transition = "transform 0.5s ease-in-out"; // más fluida
  });

  function hideAllSections() {
    sections.forEach(s => s.classList.remove('active'));
  }

  function showUbicacion() {
    mapCont.style.display = '';
    detailsCont.style.display = '';
  }

  leftTab.addEventListener('click', () => {
    tabs.forEach(t => {
      t.style.transform = '';
      t.classList.remove('activa');
    });
    showUbicacion();
    hideAllSections();
  });

  tabs.forEach((tab, idx) => {
    tab.addEventListener('click', () => {
      const baseRight = leftTab.getBoundingClientRect().right;
      const tabW = tabs[0].offsetWidth;

      if (tab.classList.contains('activa')) {
        for (let i = idx; i < tabs.length; i++) {
          const t = tabs[i];
          if (t.classList.contains('activa')) {
            t.style.transform = '';
            t.classList.remove('activa');
          }
        }
        hideAllSections();
        mapCont.style.display = 'none';
        detailsCont.style.display = 'none';

        let found = false;
        for (let i = idx - 1; i >= 0; i--) {
          if (tabs[i].classList.contains('activa')) {
            const key = tabs[i].textContent.trim()
              .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
              .toLowerCase().replace(/\s+/g, '-');
            const sec = document.getElementById(`seccion-${key}`);
            if (sec) {
              sec.classList.add('active');
              const activas = tabs.filter(t => t.classList.contains('activa')).length;
              sec.style.paddingLeft = `${(activas + 1) * 50}px`;
              found = true;
              break;
            }
          }
        }
        if (!found) {
          showUbicacion();
        }
        return;
      }

      for (let i = 0; i <= idx; i++) {
        const t = tabs[i];
        if (t.classList.contains('activa')) continue;
        const originalLeft = t.getBoundingClientRect().left;
        const targetX = baseRight + i * tabW;
        const shiftX = targetX - originalLeft;
        t.style.transform = `translateX(${shiftX}px)`;
        t.classList.add('activa');
      }

      mapCont.style.display     = 'none';
      detailsCont.style.display = 'none';
      hideAllSections();

      const key = tab.textContent.trim()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .toLowerCase().replace(/\s+/g, '-');
      const sec = document.getElementById(`seccion-${key}`);
      if (sec) {
        sec.classList.add('active');
        const activas = tabs.filter(t => t.classList.contains('activa')).length;
        sec.style.paddingLeft = `${(activas + 1) * 50}px`;
      }
    });
  });

  leftTab.click(); // disparo inicial

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
