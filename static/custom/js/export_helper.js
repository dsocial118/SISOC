/**
 * export_helper.js
 * Maneja la lógica para los botones de exportación a CSV.
 * Captura filtros de la URL y estado de ordenamiento de la tabla.
 */

document.addEventListener('DOMContentLoaded', function() {
    const exportButtons = document.querySelectorAll('.btn-export-csv');

    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const baseUrl = this.getAttribute('data-url');
            if (!baseUrl) return;

            // 1. Obtener parámetros actuales de la URL (filtros)
            const currentParams = new URLSearchParams(window.location.search);
            
            // 2. Buscar estado de ordenamiento en la tabla (si existe)
            // Asume que listSort.js marca los th con .sort-asc o .sort-desc
            const sortedHeader = document.querySelector('th.sortable.sort-asc, th.sortable.sort-desc');
            
            if (sortedHeader) {
                const column = sortedHeader.getAttribute('data-column');
                const direction = sortedHeader.classList.contains('sort-asc') ? 'asc' : 'desc';
                
                if (column) {
                    currentParams.set('sort', column);
                    currentParams.set('direction', direction);
                }
            }

            // 3. Construir URL final
            // Asegurarse de no duplicar ? si ya existe en baseUrl (raro en Django urls pero posible)
            const separator = baseUrl.includes('?') ? '&' : '?';
            const finalUrl = `${baseUrl}${separator}${currentParams.toString()}`;

            // 4. Trigger descarga
            window.location.href = finalUrl;
        });
    });
});
