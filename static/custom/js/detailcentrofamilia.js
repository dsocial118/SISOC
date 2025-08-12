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

// Ejecutar al cargar el DOM
window.addEventListener('DOMContentLoaded', ajustarAnchos);

function toggleAccordion(panel) {
    const allPanels = document.querySelectorAll('.accordion-panel');
    const totalPanels = allPanels.length;
    const closedWidth = 60; // px

    // Si el panel ya está abierto, cerrarlo y resetear anchos
    if (panel.classList.contains('open')) {
        panel.classList.remove('open');
        allPanels.forEach(p => p.style.width = closedWidth + 'px');
        return;
    }

    // Cerrar todos
    allPanels.forEach(p => p.classList.remove('open'));

    // Abrir el seleccionado
    panel.classList.add('open');

    // Calcular ancho para panel abierto
    const openWidth = `calc(100% - ${(totalPanels - 1) * closedWidth}px)`;

    // Asignar ancho a cada panel
    allPanels.forEach(p => {
        if (p.classList.contains('open')) {
            p.style.width = openWidth;
        } else {
            p.style.width = closedWidth + 'px';
        }
    });
}
