document.addEventListener("DOMContentLoaded", function () {

  /* ==========================================================
     1) FUNCIONES DE ACORDEÓN RESPONSIVE
  ========================================================== */
  function isMobile() {
    return window.innerWidth <= 768;
  }

  function ajustarAnchos() {
    const allPanels = document.querySelectorAll('.accordion-panel');
    const totalPanels = allPanels.length;
    const closedWidth = 60;

    if (isMobile()) {
      // En móvil, todos los paneles ocupan 100% y se apilan
      allPanels.forEach(p => p.style.width = '100%');
      return;
    }

    // Desktop: calcular ancho horizontal
    const openPanel = Array.from(allPanels).find(p => p.classList.contains('open'));
    if (!openPanel) {
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
    const closedWidth = 60;
  
    if (isMobile()) {
      // móvil: abrir/cerrar contenido
      panel.classList.toggle('open');
      return;
    }
  
    const index = Array.from(allPanels).indexOf(panel);
    const esPrimero = index === 0;
    const esUltimo = index === totalPanels - 1;
  
    // Si ya está abierto, no hacemos nada (no cerrar)
    if (panel.classList.contains('open')) {
      return; 
    }
  
    // Cerrar todos los demás
    allPanels.forEach(p => p.classList.remove('open'));
    panel.classList.add('open');
  
    const openWidth = `calc(100% - ${(totalPanels - 1) * closedWidth}px)`;
    allPanels.forEach(p => {
      p.style.width = p.classList.contains('open') ? openWidth : closedWidth + 'px';
    });
  }

  // Inicializar acordeón al cargar
  ajustarAnchos();

  // Evento para hacer clic solo en headers
  document.querySelectorAll('.accordion-panel .accordion-header').forEach(header => {
    header.addEventListener('click', (e) => {
      const panel = e.currentTarget.parentElement;
      toggleAccordion(panel);
    });
  });

  // Recalcular anchos al cambiar tamaño de ventana
  window.addEventListener('resize', ajustarAnchos);

});