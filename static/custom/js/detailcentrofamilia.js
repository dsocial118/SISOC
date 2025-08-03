document.addEventListener('DOMContentLoaded', () => {
  const locCard     = document.querySelector('.location-card');
  const leftTab     = document.getElementById('tab-ubicacion');
  const rightTabs   = locCard.querySelector('.right-tabs');
  const tabs        = Array.from(rightTabs.children);
  const mapCont     = document.getElementById('mapa-iframe');
  const detailsCont = document.getElementById('detalles-ubicacion');
  const sections    = Array.from(locCard.querySelectorAll('.content-seccion'));

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
        // Volver a la posición original desde esta pestaña hacia la derecha
        for (let i = idx; i < tabs.length; i++) {
          const t = tabs[i];
          if (t.classList.contains('activa')) {
            t.style.transform = '';
            t.classList.remove('activa');
          }
        }

        // Ocultar todo
        hideAllSections();
        mapCont.style.display = 'none';
        detailsCont.style.display = 'none';

        // Buscar la última pestaña activa anterior
        let found = false;
        for (let i = idx - 1; i >= 0; i--) {
          if (tabs[i].classList.contains('activa')) {
            const key = tabs[i].textContent.trim()
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .toLowerCase()
              .replace(/\s+/g, '-');

            const sec = document.getElementById(`seccion-${key}`);
            if (sec) {
              sec.classList.add('active');
              const activas = tabs.filter(t => t.classList.contains('activa')).length;
              const espacioIzquierdo = (activas + 1) * 50;
              sec.style.paddingLeft = `${espacioIzquierdo}px`;
              found = true;
              break;
            }
          }
        }

        // Si no hay ninguna activa a la izquierda, mostrar ubicación
        if (!found) {
          showUbicacion();
        }

        return;
      }

      // Activar pestañas hacia la izquierda
      for (let i = 0; i <= idx; i++) {
        const t = tabs[i];
        if (t.classList.contains('activa')) continue;

        const originalLeft = t.getBoundingClientRect().left;
        const targetX = baseRight + i * tabW;
        const shiftX = targetX - originalLeft;

        t.style.transform = `translateX(${shiftX}px)`;
        t.classList.add('activa');
      }

      // ocultar mapa y detalles
      mapCont.style.display     = 'none';
      detailsCont.style.display = 'none';
      hideAllSections();

      // mostrar la sección correspondiente
      const key = tab.textContent.trim()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/\s+/g, '-');

      const sec = document.getElementById(`seccion-${key}`);
      if (sec) {
        sec.classList.add('active');
        const activas = tabs.filter(t => t.classList.contains('activa')).length;
        const espacioIzquierdo = (activas + 1) * 50;
        sec.style.paddingLeft = `${espacioIzquierdo}px`;
      }
    });
  });

  // disparo inicial
  leftTab.click();
});
