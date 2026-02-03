/* 
 * Pagination Fix for Celiaquia Module
 * Fixes the issue where data is lost when navigating to page 2
 * when uploading files with many records
 */

document.addEventListener('DOMContentLoaded', function() {
  // Fix for preview pagination data loss
  function fixPreviewPagination() {
    const previewTable = document.getElementById('preview-table');
    const previewTbody = document.getElementById('preview-tbody');
    const previewPageSize = document.getElementById('preview-page-size');
    const previewPagination = document.getElementById('preview-pagination');
    
    if (!previewTable || !previewTbody || !previewPageSize || !previewPagination) {
      return;
    }

    // Store original data to prevent loss
    const originalRows = Array.from(previewTbody.querySelectorAll('.preview-row')).map(row => ({
      element: row.cloneNode(true),
      html: row.outerHTML
    }));

    if (originalRows.length === 0) {
      return;
    }

    let currentPage = 1;

    function renderPreviewPage() {
      const pageSize = previewPageSize.value === 'all' ? originalRows.length : parseInt(previewPageSize.value) || 10;
      const totalPages = Math.ceil(originalRows.length / pageSize);
      
      if (currentPage > totalPages && totalPages > 0) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      // Clear tbody and add only current page rows
      previewTbody.innerHTML = '';
      
      for (let i = start; i < end && i < originalRows.length; i++) {
        const clonedRow = originalRows[i].element.cloneNode(true);
        previewTbody.appendChild(clonedRow);
      }
      
      console.log(`Preview: Showing ${Math.min(end - start, originalRows.length - start)} of ${originalRows.length} rows (page ${currentPage}/${totalPages}, size: ${pageSize})`);

      // Update pagination controls
      updatePreviewPaginationControls(currentPage, totalPages);
    }

    function updatePreviewPaginationControls(page, totalPages) {
      previewPagination.innerHTML = '';

      if (totalPages <= 1) {
        previewPagination.style.display = 'none';
        return;
      }

      previewPagination.style.display = '';

      // Previous button
      const prevLi = document.createElement('li');
      prevLi.className = `page-item${page === 1 ? ' disabled' : ''}`;
      prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Anterior">&laquo;</a>`;
      if (page > 1) {
        prevLi.addEventListener('click', (e) => {
          e.preventDefault();
          currentPage--;
          renderPreviewPage();
        });
      }
      previewPagination.appendChild(prevLi);

      // Page numbers (show max 5 pages)
      let startPage = Math.max(1, page - 2);
      let endPage = Math.min(totalPages, startPage + 4);
      
      if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
      }

      // First page if not visible
      if (startPage > 1) {
        const firstLi = document.createElement('li');
        firstLi.className = 'page-item';
        firstLi.innerHTML = '<a class="page-link" href="#">1</a>';
        firstLi.addEventListener('click', (e) => {
          e.preventDefault();
          currentPage = 1;
          renderPreviewPage();
        });
        previewPagination.appendChild(firstLi);

        if (startPage > 2) {
          const dotsLi = document.createElement('li');
          dotsLi.className = 'page-item disabled';
          dotsLi.innerHTML = '<span class="page-link">...</span>';
          previewPagination.appendChild(dotsLi);
        }
      }

      // Visible page range
      for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item${i === page ? ' active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        li.addEventListener('click', (e) => {
          e.preventDefault();
          currentPage = i;
          renderPreviewPage();
        });
        previewPagination.appendChild(li);
      }

      // Last page if not visible
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          const dotsLi = document.createElement('li');
          dotsLi.className = 'page-item disabled';
          dotsLi.innerHTML = '<span class="page-link">...</span>';
          previewPagination.appendChild(dotsLi);
        }
        
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
        lastLi.addEventListener('click', (e) => {
          e.preventDefault();
          currentPage = totalPages;
          renderPreviewPage();
        });
        previewPagination.appendChild(lastLi);
      }

      // Next button
      const nextLi = document.createElement('li');
      nextLi.className = `page-item${page === totalPages ? ' disabled' : ''}`;
      nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Siguiente">&raquo;</a>`;
      if (page < totalPages) {
        nextLi.addEventListener('click', (e) => {
          e.preventDefault();
          currentPage++;
          renderPreviewPage();
        });
      }
      previewPagination.appendChild(nextLi);
    }

    // Mark as fixed and add change handler
    previewPageSize.setAttribute('data-fixed', 'true');
    
    // Remove any existing event listeners
    const newPreviewSelect = previewPageSize.cloneNode(true);
    previewPageSize.parentNode.replaceChild(newPreviewSelect, previewPageSize);
    
    // Re-get the element reference
    const updatedPreviewPageSize = document.getElementById('preview-page-size');
    updatedPreviewPageSize.setAttribute('data-fixed', 'true');
    
    updatedPreviewPageSize.addEventListener('change', function() {
      console.log('Preview page size changed to:', this.value);
      currentPage = 1;
      renderPreviewPage();
    });

    // Set initial page size from selector and render
    setTimeout(() => {
      renderPreviewPage();
    }, 50);

    // Initial render
    renderPreviewPage();
  }

  // Fix for legajos pagination data loss
  function fixLegajosPagination() {
    const legajosPageSize = document.getElementById('legajos-page-size');
    const legajosPagination = document.getElementById('legajos-pagination');
    const filtroEstado = document.getElementById('filtro-estado');
    const tbody = document.querySelector('tbody');
    
    if (!legajosPageSize || !legajosPagination || !tbody) {
      return;
    }

    // Store original legajo rows
    const originalLegajos = Array.from(tbody.querySelectorAll('tr:not(.collapse)')).map(row => {
      // Extract state from badge
      let estado = 'PENDIENTE';
      const badges = row.querySelectorAll('.badge');
      badges.forEach(badge => {
        const texto = badge.textContent.trim();
        if (['Aprobado', 'Rechazado', 'Subsanar', 'Subsanado', 'Pendiente'].includes(texto)) {
          if (texto === 'Aprobado') estado = 'APROBADO';
          else if (texto === 'Rechazado') estado = 'RECHAZADO';
          else if (texto === 'Subsanar') estado = 'SUBSANAR';
          else if (texto === 'Subsanado') estado = 'SUBSANADO';
          else if (texto === 'Pendiente') estado = 'PENDIENTE';
        }
      });
      
      return {
        element: row.cloneNode(true),
        estado: estado
      };
    });

    if (originalLegajos.length === 0) {
      return;
    }

    let currentPage = 1;
    let currentFilter = '';

    function getFilteredLegajos() {
      if (!currentFilter) {
        return originalLegajos;
      }
      return originalLegajos.filter(legajo => legajo.estado === currentFilter);
    }

    function renderLegajosPage() {
      const filteredLegajos = getFilteredLegajos();
      const pageSize = legajosPageSize.value === 'all' ? filteredLegajos.length : parseInt(legajosPageSize.value) || 10;
      const totalPages = Math.ceil(filteredLegajos.length / pageSize);
      
      if (currentPage > totalPages && totalPages > 0) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;
      
      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      // Remove existing legajo rows (not collapse rows)
      const existingRows = tbody.querySelectorAll('tr:not(.collapse)');
      existingRows.forEach(row => row.remove());

      // Add current page rows
      const rowsToShow = filteredLegajos.slice(start, end);
      rowsToShow.forEach(legajoData => {
        const clonedRow = legajoData.element.cloneNode(true);
        
        // Reactivate collapse buttons
        const collapseButtons = clonedRow.querySelectorAll('button[data-bs-toggle="collapse"]');
        collapseButtons.forEach(btn => {
          btn.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            const collapseElement = document.querySelector(target);
            if (collapseElement && window.bootstrap) {
              const bsCollapse = new bootstrap.Collapse(collapseElement, {
                toggle: false
              });
              bsCollapse.toggle();
            }
          });
        });
        
        tbody.appendChild(clonedRow);
      });
      
      console.log(`Legajos: Showing ${rowsToShow.length} of ${filteredLegajos.length} filtered rows (page ${currentPage}/${totalPages}, size: ${pageSize}, filter: '${currentFilter}')`);

      // Update pagination controls
      updateLegajosPaginationControls(currentPage, totalPages);
    }

    function updateLegajosPaginationControls(page, totalPages) {
      legajosPagination.innerHTML = '';
      
      if (totalPages <= 1) {
        legajosPagination.style.display = 'none';
        return;
      }

      legajosPagination.style.display = '';

      // Previous button
      const prevLi = document.createElement('li');
      prevLi.className = `page-item${page === 1 ? ' disabled' : ''}`;
      prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Anterior">&laquo;</a>`;
      if (page > 1) {
        prevLi.onclick = (e) => {
          e.preventDefault();
          currentPage--;
          renderLegajosPage();
        };
      }
      legajosPagination.appendChild(prevLi);

      // Page numbers
      let startPage = Math.max(1, page - 2);
      let endPage = Math.min(totalPages, startPage + 4);
      
      if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
      }

      // First page if not visible
      if (startPage > 1) {
        const firstLi = document.createElement('li');
        firstLi.className = 'page-item';
        firstLi.innerHTML = '<a class="page-link" href="#">1</a>';
        firstLi.onclick = (e) => {
          e.preventDefault();
          currentPage = 1;
          renderLegajosPage();
        };
        legajosPagination.appendChild(firstLi);

        if (startPage > 2) {
          const dotsLi = document.createElement('li');
          dotsLi.className = 'page-item disabled';
          dotsLi.innerHTML = '<span class="page-link">...</span>';
          legajosPagination.appendChild(dotsLi);
        }
      }

      // Visible page range
      for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item${i === page ? ' active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        li.onclick = (e) => {
          e.preventDefault();
          currentPage = i;
          renderLegajosPage();
        };
        legajosPagination.appendChild(li);
      }

      // Last page if not visible
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          const dotsLi = document.createElement('li');
          dotsLi.className = 'page-item disabled';
          dotsLi.innerHTML = '<span class="page-link">...</span>';
          legajosPagination.appendChild(dotsLi);
        }
        
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
        lastLi.onclick = (e) => {
          e.preventDefault();
          currentPage = totalPages;
          renderLegajosPage();
        };
        legajosPagination.appendChild(lastLi);
      }

      // Next button
      const nextLi = document.createElement('li');
      nextLi.className = `page-item${page === totalPages ? ' disabled' : ''}`;
      nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Siguiente">&raquo;</a>`;
      if (page < totalPages) {
        nextLi.onclick = (e) => {
          e.preventDefault();
          currentPage++;
          renderLegajosPage();
        };
      }
      legajosPagination.appendChild(nextLi);
    }

    // Mark as fixed and add change handler
    legajosPageSize.setAttribute('data-fixed', 'true');
    
    // Remove any existing event listeners
    const newLegajosSelect = legajosPageSize.cloneNode(true);
    legajosPageSize.parentNode.replaceChild(newLegajosSelect, legajosPageSize);
    
    // Re-get the element reference
    const updatedLegajosPageSize = document.getElementById('legajos-page-size');
    updatedLegajosPageSize.setAttribute('data-fixed', 'true');
    
    updatedLegajosPageSize.addEventListener('change', function() {
      console.log('Legajos page size changed to:', this.value);
      currentPage = 1;
      renderLegajosPage();
    });

    // Set initial page size from selector and render
    setTimeout(() => {
      renderLegajosPage();
    }, 50);

    // Filter removed - show all records

    // Initial render
    renderLegajosPage();
  }

  // Override any conflicting pagination handlers
  function overrideConflictingHandlers() {
    // Remove existing event listeners that might conflict
    const previewPageSize = document.getElementById('preview-page-size');
    const legajosPageSize = document.getElementById('legajos-page-size');
    
    if (previewPageSize) {
      const newPreviewSelect = previewPageSize.cloneNode(true);
      previewPageSize.parentNode.replaceChild(newPreviewSelect, previewPageSize);
    }
    
    if (legajosPageSize) {
      const newLegajosSelect = legajosPageSize.cloneNode(true);
      legajosPageSize.parentNode.replaceChild(newLegajosSelect, legajosPageSize);
    }
  }

  // Initialize fixes with delay to ensure DOM is ready
  setTimeout(() => {
    overrideConflictingHandlers();
    fixPreviewPagination();
    fixLegajosPagination();
  }, 300);

  // Additional check to ensure selectors work
  setTimeout(() => {
    const previewPageSize = document.getElementById('preview-page-size');
    const legajosPageSize = document.getElementById('legajos-page-size');
    
    if (previewPageSize && !previewPageSize.hasAttribute('data-fixed')) {
      previewPageSize.setAttribute('data-fixed', 'true');
      fixPreviewPagination();
    }
    
    if (legajosPageSize && !legajosPageSize.hasAttribute('data-fixed')) {
      legajosPageSize.setAttribute('data-fixed', 'true');
      fixLegajosPagination();
    }
  }, 500);

  // Test function to verify page size selectors work
  window.testPageSizeSelectors = function() {
    const previewPageSize = document.getElementById('preview-page-size');
    const legajosPageSize = document.getElementById('legajos-page-size');
    
    console.log('Testing page size selectors...');
    
    if (previewPageSize) {
      console.log('Preview selector found, current value:', previewPageSize.value);
      console.log('Preview selector has change listener:', previewPageSize.hasAttribute('data-fixed'));
    }
    
    if (legajosPageSize) {
      console.log('Legajos selector found, current value:', legajosPageSize.value);
      console.log('Legajos selector has change listener:', legajosPageSize.hasAttribute('data-fixed'));
    }
    
    return {
      previewWorking: previewPageSize && previewPageSize.hasAttribute('data-fixed'),
      legajosWorking: legajosPageSize && legajosPageSize.hasAttribute('data-fixed')
    };
  };
});
