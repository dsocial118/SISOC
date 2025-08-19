/* static/custom/js/expediente_detail.js
 * - Procesar expediente
 * - Subir/editar archivo de legajo
 * - Confirmar Envío
 * - Subir/Reprocesar Excel de CUITs y ejecutar cruce (técnico)
 * - Paginación client-side para Preview y Legajos (con selector de tamaño de página)
 */

document.addEventListener('DOMContentLoaded', () => {
  /* ===== Helpers básicos ===== */
  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return m ? m[2] : null;
  }
  function getCsrfToken() {
    return (typeof window !== 'undefined' && window.CSRF_TOKEN) || getCookie('csrftoken');
  }
  function ensureAlertsZone() {
    let zone = document.getElementById('expediente-alerts');
    if (!zone) {
      zone = document.createElement('div');
      zone.id = 'expediente-alerts';
      const headerBlock = document.querySelector('.p-3.rounded.shadow.mb-4');
      (headerBlock || document.body).prepend(zone);
    }
    return zone;
  }

  /* ====== Paginación genérica client-side ====== */
  function paginate({
    items,                   // NodeList/Array de elementos a paginar
    pageSizeSelect,          // <select> para tamaño de página
    paginationUl,            // <ul> .pagination para los botones
    onPageChange,            // callback opcional cuando cambia de página
    hideIfSinglePage = true, // oculta la barra si hay 0/1 páginas
  }) {
    const nodes = Array.from(items);
    if (!nodes.length || !pageSizeSelect || !paginationUl) return;

    let page = 1;
    const readPageSize = () => parseInt(pageSizeSelect.value || '10', 10) || 10;

    function render() {
      const pageSize = readPageSize();
      const total = nodes.length;
      const totalPages = Math.max(1, Math.ceil(total / pageSize));
      if (page > totalPages) page = totalPages;

      // Mostrar/ocultar items
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      nodes.forEach((el, i) => {
        el.style.display = (i >= start && i < end) ? '' : 'none';
      });

      // Render paginador
      paginationUl.innerHTML = '';
      if (hideIfSinglePage && totalPages <= 1) {
        paginationUl.style.display = 'none';
      } else {
        paginationUl.style.display = '';
        const liPrev = document.createElement('li');
        liPrev.className = `page-item${page === 1 ? ' disabled' : ''}`;
        liPrev.innerHTML = `<a class="page-link" href="#" aria-label="Anterior">&laquo;</a>`;
        liPrev.addEventListener('click', (e) => { e.preventDefault(); if (page > 1) { page--; render(); }});
        paginationUl.appendChild(liPrev);

        // Máx 7 botones (compacto)
        const maxBtns = 7;
        let startPage = Math.max(1, page - 3);
        let endPage = Math.min(totalPages, startPage + maxBtns - 1);
        if (endPage - startPage + 1 < maxBtns) startPage = Math.max(1, endPage - maxBtns + 1);

        if (startPage > 1) {
          const liFirst = document.createElement('li');
          liFirst.className = 'page-item';
          liFirst.innerHTML = `<a class="page-link" href="#">1</a>`;
          liFirst.addEventListener('click', (e) => { e.preventDefault(); page = 1; render(); });
          paginationUl.appendChild(liFirst);

          if (startPage > 2) {
            const liDots = document.createElement('li');
            liDots.className = 'page-item disabled';
            liDots.innerHTML = `<a class="page-link" href="#">…</a>`;
            paginationUl.appendChild(liDots);
          }
        }

        for (let p = startPage; p <= endPage; p++) {
          const li = document.createElement('li');
          li.className = `page-item${p === page ? ' active' : ''}`;
          li.innerHTML = `<a class="page-link" href="#">${p}</a>`;
          li.addEventListener('click', (e) => { e.preventDefault(); page = p; render(); });
          paginationUl.appendChild(li);
        }

        if (endPage < totalPages) {
          if (endPage < totalPages - 1) {
            const liDots2 = document.createElement('li');
            liDots2.className = 'page-item disabled';
            liDots2.innerHTML = `<a class="page-link" href="#">…</a>`;
            paginationUl.appendChild(liDots2);
          }
          const liLast = document.createElement('li');
          liLast.className = 'page-item';
          liLast.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
          liLast.addEventListener('click', (e) => { e.preventDefault(); page = totalPages; render(); });
          paginationUl.appendChild(liLast);
        }

        const liNext = document.createElement('li');
        liNext.className = `page-item${page === totalPages ? ' disabled' : ''}`;
        liNext.innerHTML = `<a class="page-link" href="#" aria-label="Siguiente">&raquo;</a>`;
        liNext.addEventListener('click', (e) => { e.preventDefault(); if (page < totalPages) { page++; render(); }});
        paginationUl.appendChild(liNext);
      }

      if (typeof onPageChange === 'function') onPageChange({ page, pageSize: readPageSize(), total: nodes.length });
    }

    pageSizeSelect.addEventListener('change', () => { page = 1; render(); });
    render();
    return { goto: (p) => { page = p; render(); } };
  }

  /* ===== PROCESAR EXPEDIENTE ===== */
  const btnProcess = document.getElementById('btn-process-expediente');
  if (btnProcess) {
    const msgContainer = document.createElement('div');
    msgContainer.id = 'process-msg';
    const previewCard = document.querySelector('.card.mb-4');
    if (previewCard) previewCard.parentNode.insertBefore(msgContainer, previewCard);

    btnProcess.addEventListener('click', async () => {
      btnProcess.disabled = true;
      const origHTML = btnProcess.innerHTML;
      btnProcess.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...';

      try {
        const resp = await fetch(window.PROCESS_URL, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });

        const raw = await resp.text();
        if (resp.status !== 200) throw new Error(`HTTP ${resp.status}: ${raw.trim()}`);
        const data = JSON.parse(raw);
        if (!data.success) throw new Error(data.error || 'Server returned success=false');

        msgContainer.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            <strong>¡Listo!</strong> Se crearon ${data.creados} legajos.
            El expediente pasó a <strong>EN ESPERA</strong>.
            ${data.errores ? `<br><small class="text-danger">${data.errores} errores.</small>` : ''}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        setTimeout(() => window.location.reload(), 1200);

      } catch (err) {
        console.error('Error procesar expediente:', err);
        msgContainer.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            Error al procesar expediente: ${err.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        btnProcess.disabled = false;
      } finally {
        btnProcess.innerHTML = origHTML;
      }
    });
  }

  /* ===== MODAL SUBIR/EDITAR ARCHIVO DE LEGAJO ===== */
  const modalArchivo = document.getElementById('modalSubirArchivo');
  if (modalArchivo) {
    modalArchivo.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const legajoId = button.getAttribute('data-legajo-id');
      const expedienteId = button.getAttribute('data-expediente-id');
      const form = modalArchivo.querySelector('#form-subir-archivo');

      const actionUrl = `/expedientes/${expedienteId}/ciudadanos/${legajoId}/archivo/`;
      form.setAttribute('action', actionUrl);

      const inputArchivo = form.querySelector('input[type="file"]');
      if (inputArchivo) inputArchivo.value = '';

      const alertas = modalArchivo.querySelector('#modal-alertas');
      if (alertas) alertas.innerHTML = '';
    });

    const form = document.getElementById('form-subir-archivo');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = form.getAttribute('action');
      const formData = new FormData(form);
      const btnSubmit = form.querySelector('button[type="submit"]');
      const originalHTML = btnSubmit.innerHTML;
      const alertas = modalArchivo.querySelector('#modal-alertas');

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Subiendo...';

      try {
        const resp = await fetch(url, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        const data = await resp.json();
        if (!data.success) throw new Error(data.message || 'Error desconocido');

        alertas.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${data.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;

        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalArchivo);
          modal.hide();
          window.location.reload();
        }, 1000);

      } catch (err) {
        alertas.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${err.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        console.error('Error al subir archivo:', err);
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalHTML;
      }
    });
  }

  /* ===== CONFIRMAR ENVÍO ===== */
  const btnConfirm = document.getElementById('btn-confirm');
  if (btnConfirm) {
    let alertZone = ensureAlertsZone();

    btnConfirm.addEventListener('click', async () => {
      if (!window.CONFIRM_URL) {
        alertZone.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            No se configuró la URL de confirmación.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
        return;
      }

      btnConfirm.disabled = true;
      const original = btnConfirm.innerHTML;
      btnConfirm.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando…';

      try {
        const resp = await fetch(window.CONFIRM_URL, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });

        let data = {};
        const ct = resp.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) {
          data = await resp.json();
        } else {
          const text = await resp.text();
          if (!resp.ok) throw new Error(text || `HTTP ${resp.status}`);
          data = { success: true, message: text };
        }

        if (!resp.ok || data.success === false) {
          const msg = data.error || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        alertZone.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${data.message || 'Expediente enviado a Subsecretaría.'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;

        setTimeout(() => window.location.reload(), 700);

      } catch (err) {
        console.error('Error al confirmar envío:', err);
        alertZone.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            No se pudo confirmar el envío. ${err.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = original;
      }
    });
  }

  /* ===== CRUCE CUIT (Nuevo/Reprocesar) ===== */
  const modalCruce = document.getElementById('modalCruceCuit');
  if (modalCruce) {
    const formCruce = document.getElementById('form-cruce-cuit');
    const alertasCruce = document.getElementById('cruce-alertas');
    const titleEl = document.getElementById('modalCruceCuitLabel');
    const helpEl  = document.getElementById('cruce-help');
    const btnSubmit = document.getElementById('btn-cruce-submit');

    // Cambiamos el título/ayuda según el botón que abre el modal
    modalCruce.addEventListener('show.bs.modal', (e) => {
      const trigger = e.relatedTarget;
      const mode = (trigger && trigger.getAttribute('data-mode')) || 'new';

      if (mode === 'reprocess') {
        titleEl.textContent = 'Reprocesar Cruce (sobrescribe el archivo anterior)';
        helpEl.innerHTML = 'Esta acción <b>sobrescribirá</b> el archivo previo. Columnas válidas: <strong>cuit</strong> o <strong>dni</strong>.';
        btnSubmit.textContent = 'Reprocesar';
        btnSubmit.classList.remove('btn-success');
        btnSubmit.classList.add('btn-warning');
      } else {
        titleEl.textContent = 'Subir Excel de CUITs/DNIs (con encabezado)';
        helpEl.textContent = 'Debe incluir encabezado; columnas válidas: cuit o dni.';
        btnSubmit.textContent = 'Ejecutar Cruce';
        btnSubmit.classList.remove('btn-warning');
        btnSubmit.classList.add('btn-success');
      }

      alertasCruce.innerHTML = '';
      const input = document.getElementById('id_excel_cuit');
      if (input) input.value = '';
    });

    formCruce.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!window.CRUCE_URL) {
        alertasCruce.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            No se configuró la URL de cruce.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
        return;
      }

      const input = document.getElementById('id_excel_cuit');
      if (!input || !input.files || !input.files.length) {
        alertasCruce.innerHTML = `
          <div class="alert alert-warning alert-dismissible fade show" role="alert">
            Seleccioná un archivo con columna <strong>cuit</strong> o <strong>dni</strong>.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
        return;
      }

      const originalHTML = btnSubmit.innerHTML;
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando…';
      alertasCruce.innerHTML = '';

      try {
        const fd = new FormData(formCruce);
        // La view espera 'archivo':
        fd.delete('excel_cuit');
        fd.append('archivo', input.files[0]);

        const resp = await fetch(window.CRUCE_URL, {
          method: 'POST',
          body: fd,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });

        const ct = resp.headers.get('Content-Type') || '';
        let data = {};
        if (ct.includes('application/json')) {
          data = await resp.json();
        } else {
          const text = await resp.text();
          if (!resp.ok) throw new Error(text || `HTTP ${resp.status}`);
          data = { success: true, message: text };
        }

        if (!resp.ok || data.success === false) {
          const msg = data.error || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        // Detalle/PRD opcionales (si el backend los envía)
        const detalle = (data.detalle && `
          <ul class="mb-0">
            <li><strong>Leídos:</strong> ${data.detalle.leidos ?? '-'}</li>
            <li><strong>Match:</strong> ${data.detalle.match ?? '-'}</li>
            <li><strong>No encontrados:</strong> ${data.detalle.no_encontrados ?? '-'}</li>
          </ul>
        `) || '';

        const prdLink = (data.prd_url && `
          <div class="mt-2">
            <a href="${data.prd_url}" target="_blank" class="btn btn-sm btn-outline-light">Ver PRD generado</a>
          </div>
        `) || '';

        alertasCruce.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${data.message || 'Cruce ejecutado correctamente.'}
            ${detalle}
            ${prdLink}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;

        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalCruce);
          modal.hide();
          window.location.reload();
        }, 1200);

      } catch (err) {
        console.error('Cruce CUIT:', err);
        alertasCruce.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            No se pudo ejecutar el cruce. ${err.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>`;
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalHTML;
      }
    });
  }

  /* ===== Inicializar paginación para PREVIEW ===== */
  (function initPreviewPagination(){
    const tbody = document.getElementById('preview-tbody');
    const pageSizeSel = document.getElementById('preview-page-size');
    const pagUl = document.getElementById('preview-pagination');
    if (!tbody || !pageSizeSel || !pagUl) return;

    paginate({
      items: tbody.querySelectorAll('.preview-row'),
      pageSizeSelect: pageSizeSel,
      paginationUl: pagUl,
      onPageChange: null,
    });
  })();

  /* ===== Inicializar paginación para LEGAJOS ===== */
  (function initLegajosPagination(){
    const list = document.getElementById('legajos-list');
    const pageSizeSel = document.getElementById('legajos-page-size');
    const pagUl = document.getElementById('legajos-pagination');
    if (!list || !pageSizeSel || !pagUl) return;

    paginate({
      items: list.querySelectorAll('.legajo-item'),
      pageSizeSelect: pageSizeSel,
      paginationUl: pagUl,
      onPageChange: null,
    });
  })();
});
