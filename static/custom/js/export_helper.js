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

            // 3. Construir URL final de forma segura a partir de baseUrl
            let exportUrl;
            try {
                // Permite rutas relativas y absolutas, siempre respecto al origen actual
                exportUrl = new URL(baseUrl, window.location.href);
            } catch (err) {
                // Si baseUrl no es una URL válida, abortar
                return;
            }

            // Restringir esquema y origen para evitar redirecciones inseguras
            if ((exportUrl.protocol !== 'http:' && exportUrl.protocol !== 'https:') ||
                exportUrl.origin !== window.location.origin) {
                return;
            }

            // Añadir/mezclar parámetros actuales a la URL de exportación
            currentParams.forEach((value, key) => {
                exportUrl.searchParams.set(key, value);
            });

            const finalUrl = exportUrl.toString();

            // 4. Trigger descarga
            window.location.href = finalUrl;
        });
    });
});
