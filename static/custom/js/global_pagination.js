// Paginación global para todos los selectores
document.addEventListener('DOMContentLoaded', function() {
  const paginationStates = {};
  
  // Buscar todos los selectores de paginación
  const selectors = document.querySelectorAll('select[id$="-page-size"]');
  
  selectors.forEach(selector => {
    const selectorId = selector.id;
    const prefix = selectorId.replace('-page-size', '');
    
    paginationStates[prefix] = {
      currentPage: 1,
      pageSize: 10,
      totalItems: 0,
      items: []
    };
    
    function updatePagination(prefix, pageSize, currentPage = 1) {
      const state = paginationStates[prefix];
      
      // Buscar items relacionados
      let items = [];
      const patterns = [
        `.${prefix}-item`,
        `#${prefix}-list .${prefix}-item`,
        `#${prefix}-list .list-group-item`,
        `.${prefix.replace('-', '_')}-item`,
        '.legajo-item',
        '.preview-row'
      ];
      
      for (const pattern of patterns) {
        items = document.querySelectorAll(pattern);
        if (items.length > 0) break;
      }
      
      if (items.length === 0) return;
      
      state.items = items;
      state.totalItems = items.length;
      state.pageSize = pageSize === 'all' ? items.length : parseInt(pageSize) || 10;
      state.currentPage = currentPage;
      
      const totalPages = Math.ceil(state.totalItems / state.pageSize);
      const startIndex = (state.currentPage - 1) * state.pageSize;
      const endIndex = startIndex + state.pageSize;
      
      // Mostrar/ocultar items
      items.forEach((item, index) => {
        item.style.display = (index >= startIndex && index < endIndex) ? '' : 'none';
      });
      
      // Actualizar paginador
      updatePaginationControls(prefix, state.currentPage, totalPages);
    }
    
    function updatePaginationControls(prefix, currentPage, totalPages) {
      const paginationContainer = document.getElementById(`${prefix}-pagination`);
      if (!paginationContainer || totalPages <= 1) {
        if (paginationContainer) paginationContainer.innerHTML = '';
        return;
      }
      
      let html = '';
      
      // Flecha anterior
      if (currentPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage - 1}">&laquo;</a></li>`;
      } else {
        html += `<li class="page-item disabled"><span class="page-link">&laquo;</span></li>`;
      }
      
      // Páginas visibles (máximo 5)
      let startPage = Math.max(1, currentPage - 2);
      let endPage = Math.min(totalPages, startPage + 4);
      
      if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
      }
      
      // Primera página si no está visible
      if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
        if (startPage > 2) {
          html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
      }
      
      // Páginas del rango
      for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
          html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
          html += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
      }
      
      // Última página si no está visible
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
      }
      
      // Flecha siguiente
      if (currentPage < totalPages) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage + 1}">&raquo;</a></li>`;
      } else {
        html += `<li class="page-item disabled"><span class="page-link">&raquo;</span></li>`;
      }
      
      paginationContainer.innerHTML = html;
      
      // Event listeners para los enlaces de página
      paginationContainer.querySelectorAll('a[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
          e.preventDefault();
          const newPage = parseInt(this.dataset.page);
          updatePagination(prefix, paginationStates[prefix].pageSize, newPage);
        });
      });
    }
    
    selector.addEventListener('change', function() {
      updatePagination(prefix, this.value, 1);
    });
    
    // Trigger inicial
    updatePagination(prefix, selector.value || 10);
  });
});