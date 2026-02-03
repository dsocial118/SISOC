document.addEventListener("DOMContentLoaded", function () {

  /* ==========================================================
     1) FUNCIONES DE ACORDEÓN RESPONSIVE
  ========================================================== */
  const accordion = document.querySelector('.accordion-horizontal');
  const accordionShell = document.querySelector('.accordion-shell');
  if (accordion) {
    accordion.classList.add('is-initializing');
  }

  function terminarCarga() {
    if (accordionShell) {
      accordionShell.classList.remove('is-loading');
    }
  }

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

  function ajustarAltura() {
    const accordion = document.querySelector('.accordion-horizontal');
    if (!accordion) {
      return;
    }

    const panels = Array.from(accordion.querySelectorAll('.accordion-panel'));
    if (!panels.length) {
      return;
    }

    if (isMobile()) {
      accordion.style.height = 'auto';
      panels.forEach(panel => {
        panel.style.height = 'auto';
      });
      return;
    }

    const totalPanels = panels.length;
    const closedWidth = 60;
    const openWidth = accordion.clientWidth - (totalPanels - 1) * closedWidth;
    if (openWidth <= 0) {
      return;
    }

    const originalOpenPanel = panels.find(panel => panel.classList.contains('open')) || panels[0];

    accordion.classList.add('is-measuring');

    let maxHeight = 0;
    panels.forEach((panel, index) => {
      panels.forEach((item, itemIndex) => {
        item.classList.toggle('open', itemIndex === index);
        item.style.width = itemIndex === index ? `${openWidth}px` : `${closedWidth}px`;
      });

      const content = panel.querySelector('.accordion-content');
      if (content) {
        const contentHeight = content.scrollHeight;
        if (contentHeight > maxHeight) {
          maxHeight = contentHeight;
        }
      }
    });

    panels.forEach(panel => {
      panel.classList.toggle('open', panel === originalOpenPanel);
    });

    accordion.classList.remove('is-measuring');

    if (maxHeight > 0) {
      accordion.style.height = `${maxHeight}px`;
      panels.forEach(panel => {
        panel.style.height = `${maxHeight}px`;
      });
    }

    ajustarAnchos();
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
  requestAnimationFrame(() => {
    ajustarAltura();
    if (accordion) {
      accordion.classList.remove('is-initializing');
    }
  });

  // Evento para hacer clic solo en headers
  document.querySelectorAll('.accordion-panel .accordion-header').forEach(header => {
    header.addEventListener('click', (e) => {
      const panel = e.currentTarget.parentElement;
      toggleAccordion(panel);
    });
  });

  // Recalcular anchos al cambiar tamaño de ventana
  window.addEventListener('resize', () => {
    ajustarAnchos();
    ajustarAltura();
  });

  window.addEventListener('load', () => {
    ajustarAltura();
    terminarCarga();
  });

});
