/* static/custom/js/expediente_detail.js
 * - Procesar expediente
 * - Subir/editar archivo de legajo (archivo1/archivo2/archivo3)
 * - Confirmar Envío
 * - Subir/Reprocesar Excel de CUITs y ejecutar cruce (técnico)
 * - Revisión de legajos (Aprobar / Rechazar / Subsanar)
 *
 * Updated: showAlert now escapes user provided content via a shared
 * escapeHtml helper to avoid HTML injection.
 */

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
function showAlert(kind, ...parts) {
  const zone = ensureAlertsZone();
  const msg = parts.map((p) => escapeHtml(String(p))).join('');
  zone.innerHTML = `
      <div class="alert alert-${escapeHtml(kind)} alert-dismissible fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>`;
}

if (typeof module !== 'undefined') {
  module.exports = { showAlert };
}

document.addEventListener('DOMContentLoaded', () => {
  const editarLegajoMeta = document.querySelector('meta[name="editar-legajo-url-template"]');
  const editarLegajoUrlTemplate = (window.EDITAR_LEGAJO_URL_TEMPLATE ||
    editarLegajoMeta?.getAttribute('content')?.replace('/0/', '/{id}/')) || null;
  if (editarLegajoUrlTemplate && !window.EDITAR_LEGAJO_URL_TEMPLATE) {
    window.EDITAR_LEGAJO_URL_TEMPLATE = editarLegajoUrlTemplate;
  }

  /* ====== Paginación genérica client-side ====== */
  function paginate({
    items,
    pageSizeSelect,
    paginationUl,
    onPageChange,
    hideIfSinglePage = true,
  }) {
    const nodes = Array.from(items);
    console.log('Paginate called with:', {
      itemsCount: nodes.length,
      pageSizeSelect: pageSizeSelect?.id,
      paginationUl: paginationUl?.id,
      pageSizeSelectValue: pageSizeSelect?.value
    });

    if (!nodes.length || !pageSizeSelect || !paginationUl) {
      console.log('Paginate: missing required elements', {
        hasNodes: !!nodes.length,
        hasPageSizeSelect: !!pageSizeSelect,
        hasPaginationUl: !!paginationUl
      });
      return;
    }

    let page = 1;
    const readPageSize = () => {
      const val = pageSizeSelect.value;
      const size = val === 'all' ? Infinity : parseInt(val, 10) || 10;
      console.log('Page size:', val, '->', size, 'from element:', pageSizeSelect.id);
      return size;
    };

    function render() {
      const pageSize = readPageSize();
      const total = nodes.length;
      const totalPages = pageSize === Infinity ? 1 : Math.max(1, Math.ceil(total / pageSize));
      if (page > totalPages) page = totalPages;

      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      console.log('Renderizando página:', { page, pageSize, total, totalPages, start, end });
      nodes.forEach((el, i) => {
        const shouldShow = (i >= start && i < end);
        el.style.display = shouldShow ? '' : 'none';
        if (i < 3) console.log(`Item ${i}: ${shouldShow ? 'visible' : 'oculto'}`);
      });

      paginationUl.innerHTML = '';
      if (hideIfSinglePage && totalPages <= 1) {
        paginationUl.style.display = 'none';
      } else {
        paginationUl.style.display = '';
        const liPrev = document.createElement('li');
        liPrev.className = `page-item${page === 1 ? ' disabled' : ''}`;
        liPrev.innerHTML = `<a class="page-link" href="#" aria-label="Anterior">&laquo;</a>`;
        liPrev.addEventListener('click', (e) => { e.preventDefault(); if (page > 1) { page--; render(); } });
        paginationUl.appendChild(liPrev);

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
        liNext.addEventListener('click', (e) => { e.preventDefault(); if (page < totalPages) { page++; render(); } });
        paginationUl.appendChild(liNext);
      }

      if (typeof onPageChange === 'function') onPageChange({ page, pageSize: readPageSize(), total: nodes.length });
    }

    pageSizeSelect.addEventListener('change', (e) => {
      console.log('Selector genérico cambió a:', e.target.value);
      page = 1;
      render();
    });
    render();
    return { goto: (p) => { page = p; render(); } };
  }

  /* ===== PROCESAR EXPEDIENTE ===== */
  const btnProcess = document.getElementById('btn-process-expediente');
  if (btnProcess) {
    btnProcess.addEventListener('click', async () => {
      btnProcess.disabled = true;
      let origHTML;
      let progressInterval;

      try {
        origHTML = btnProcess.innerHTML;

        // Crear indicador de progreso
        const progressHtml = `
          <div class="d-flex align-items-center">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            <span>Procesando <span id="progress-current">0</span> / <span id="progress-total">?</span> registros...</span>
          </div>
        `;
        btnProcess.innerHTML = progressHtml;

        // Obtener total de registros del preview
        const previewRows = document.querySelectorAll('.preview-row');
        const totalRegistros = previewRows.length;
        document.getElementById('progress-total').textContent = totalRegistros;

        // Simular progreso (actualizar cada 200ms)
        let currentProgress = 0;
        const incremento = Math.max(1, Math.floor(totalRegistros / 20)); // 20 actualizaciones aprox

        progressInterval = setInterval(() => {
          if (currentProgress < totalRegistros) {
            currentProgress = Math.min(currentProgress + incremento, totalRegistros);
            const progressEl = document.getElementById('progress-current');
            if (progressEl) progressEl.textContent = currentProgress;
          }
        }, 200);

        if (!window.PROCESS_URL) throw new Error('No se configuró PROCESS_URL.');

        const resp = await fetch(window.PROCESS_URL, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });

        if (resp.redirected) {
          showAlert('danger', 'Tu sesión expiró o no tenés permisos. Volvé a iniciar sesión.');
          return;
        }

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
          const msg = data.error || data.message || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        // Completar progreso
        clearInterval(progressInterval);
        const progressCurrentEl = document.getElementById('progress-current');
        if (progressCurrentEl) progressCurrentEl.textContent = totalRegistros;

        // Mostrar "Completado" por un momento
        btnProcess.innerHTML = `
          <div class="d-flex align-items-center">
            <span class="text-success me-2">✓</span>
            <span>Completado ${totalRegistros} / ${totalRegistros} registros</span>
          </div>
        `;

        setTimeout(() => {
          const baseMsg =
            data.message ||
            `Se crearon ${data.creados ?? '-'} legajos y el expediente pasó a EN ESPERA.`;
          const errorExtra = data.errores ? ` ${data.errores} errores.` : '';
          const alertType = data.errores > 0 ? 'warning' : 'success';
          showAlert(alertType, '¡Listo! ', baseMsg, errorExtra);

          setTimeout(() => window.location.reload(), 1000);
        }, 800);

      } catch (err) {
        console.error('Error procesar expediente:', err);
        showAlert('danger', 'Error al procesar el expediente: ', err.message);
        btnProcess.innerHTML = origHTML;
        btnProcess.disabled = false;
      } finally {
        if (progressInterval) clearInterval(progressInterval);
        setTimeout(() => {
          btnProcess.innerHTML = origHTML;
          btnProcess.disabled = false;
        }, 2000);
      }
    });
  }

  /* ===== MODAL SUBIR/EDITAR ARCHIVO DE LEGAJO (archivo1/2/3) ===== */
  const modalArchivo = document.getElementById('modalSubirArchivo');
    if (modalArchivo) {
      // Asegurar z-index del modal
      modalArchivo.style.zIndex = '9999';
      const modalBackdrop = modalArchivo.querySelector('.modal-backdrop');
      if (modalBackdrop) modalBackdrop.style.zIndex = '9998';
      
      modalArchivo.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const actionUrl = button?.getAttribute('data-action-url');
        const defaultCampo = button?.getAttribute('data-file-field') || 'archivo1';
        const archivo2Label = button?.getAttribute('data-archivo2-label') || 'Documento';
        const archivo3Label = button?.getAttribute('data-archivo3-label') || 'Biopsia / Constancia médica';
        const uploadForm = modalArchivo.querySelector('#form-subir-archivo');

        if (actionUrl) {
          uploadForm.setAttribute('action', actionUrl);
        }

      const selCampo = modalArchivo.querySelector('#campo-archivo');
      if (selCampo) selCampo.value = defaultCampo;

      // Actualizar labels dinámicamente
      const optArchivo2 = document.getElementById('opt-archivo2');
      const optArchivo3 = document.getElementById('opt-archivo3');
      if (optArchivo2) optArchivo2.textContent = archivo2Label;
      if (optArchivo3) optArchivo3.textContent = archivo3Label;

      const inputArchivo = uploadForm.querySelector('input[type="file"]');
      if (inputArchivo) inputArchivo.value = '';

      const alertas = modalArchivo.querySelector('#modal-alertas');
      if (alertas) alertas.innerHTML = '';
    });

    const uploadForm = document.getElementById('form-subir-archivo');
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = uploadForm.getAttribute('action');
      const formData = new FormData(uploadForm);

      // mapear campo -> slot (2/3) que espera el backend
      const campo = (formData.get('campo') || '').toString().toLowerCase();
      const slotMap = { 'archivo2': 2, 'archivo3': 3 };
      const slot = slotMap[campo];
      if (!slot) {
        showAlert('danger', 'Campo inválido.');
        return;
      }
      formData.append('slot', String(slot));

      const btnSubmit = uploadForm.querySelector('button[type="submit"]');
      const originalHTML = btnSubmit.innerHTML;
      const alertas = modalArchivo.querySelector('#modal-alertas');

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Subiendo...';

      try {
        const resp = await fetch(url, {
          method: 'POST',
          body: formData, // incluye 'campo', 'archivo' y 'slot'
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
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

        if (!resp.ok || data.success === false) throw new Error(data.message || 'Error desconocido');

        alertas.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${data.message || 'Archivo guardado correctamente.'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;

        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalArchivo);
          modal.hide();
          window.location.reload();
        }, 800);

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

  /* ===== MODAL SUBSANAR (técnico) ===== */
  const modalSubsanar = document.getElementById('modalSubsanar');
  if (modalSubsanar) {
    // Pre-cargar el id del legajo en el hidden cuando se abre el modal
    modalSubsanar.addEventListener('show.bs.modal', function (event) {
      const trigger = event.relatedTarget;
      const legajoId = trigger?.getAttribute('data-legajo-id') || '';
      modalSubsanar.querySelector('#subsanar-legajo-id').value = legajoId;
      const ta = modalSubsanar.querySelector('#subsanar-motivo');
      if (ta) ta.value = '';
    });

    const formSubsanar = document.getElementById('form-subsanar');
    formSubsanar.addEventListener('submit', async (e) => {
      e.preventDefault();

      const legajoId = modalSubsanar.querySelector('#subsanar-legajo-id').value;
      const motivo = (modalSubsanar.querySelector('#subsanar-motivo').value || '').trim();
      const btn = document.getElementById('btn-confirm-subsanar');
      const original = btn.innerHTML;

      if (!legajoId) {
        showAlert('danger', 'No se pudo identificar el legajo.');
        return;
      }
      if (!motivo) {
        showAlert('warning', 'Indicá el motivo de la subsanación.');
        return;
      }

      // Opción 1: SIEMPRE usar RevisarLegajo (legajo_revisar)
      if (!window.REVISAR_URL_TEMPLATE) {
        showAlert('danger', 'No se configuró la URL de subsanación.');
        return;
      }
      const url = window.REVISAR_URL_TEMPLATE.replace('{id}', legajoId);

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando…';

      try {
        // Enviar exactamente lo que espera RevisarLegajoView
        const fd = new FormData();
        fd.append('accion', 'SUBSANAR');
        fd.append('motivo', motivo);

        const resp = await fetch(url, {
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
          data = { success: true, message: text, estado: 'SUBSANAR' };
        }

        if (!resp.ok || data.success === false) {
          const msg = data.error || data.message || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        if (data.message) {
          showAlert('success', data.message);
        } else {
          showAlert('success', 'Legajo ', legajoId, ': quedó en SUBSANAR.');
        }
        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalSubsanar);
          modal.hide();
          window.location.reload();
        }, 800);

      } catch (err) {
        console.error('Subsanar legajo:', err);
        showAlert('danger', 'No se pudo solicitar la subsanación. ', err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = original;
      }
    });
  }


  /* ===== CRUCE CUIT (Nuevo/Reprocesar) ===== */
  const modalCruce = document.getElementById('modalCruceCuit');
  if (modalCruce) {
    const formCruce = document.getElementById('form-cruce-cuit');
    const alertasCruce = document.getElementById('cruce-alertas');
    const titleEl = document.getElementById('modalCruceCuitLabel');
    const helpEl = document.getElementById('cruce-help');
    const btnSubmit = document.getElementById('btn-cruce-submit');

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

  /* ===== Revisión de legajos (Aprobar / Rechazar) ===== */
  (function initRevisionLegajos() {
    const buttons = document.querySelectorAll('.btn-revision');
    if (!buttons.length) return;

    function setLoading(btn, loading) {
      if (!btn) return;
      if (loading) {
        btn.dataset._orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
      } else {
        btn.disabled = false;
        if (btn.dataset._orig) {
          btn.innerHTML = btn.dataset._orig;
          delete btn.dataset._orig;
        }
      }
    }

    function toggleActive(btnAprobar, btnRechazar, estado) {
      [btnAprobar, btnRechazar].forEach(b => {
        if (!b) return;
        b.classList.remove('active');
        b.classList.remove('btn-success', 'btn-danger');
        b.classList.add('btn-outline-success');
        if (b && b.dataset.accion === 'RECHAZAR') {
          b.classList.remove('btn-outline-success');
          b.classList.add('btn-outline-danger');
        }
      });

      if (estado === 'APROBADO' && btnAprobar) {
        btnAprobar.classList.add('active');
        btnAprobar.classList.remove('btn-outline-success');
        btnAprobar.classList.add('btn-success');
      }
      if (estado === 'RECHAZADO' && btnRechazar) {
        btnRechazar.classList.add('active');
        btnRechazar.classList.remove('btn-outline-danger');
        btnRechazar.classList.add('btn-danger');
      }
    }

    buttons.forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();

        if (!window.REVISAR_URL_TEMPLATE) {
          showAlert('danger', 'No se configuró la URL de revisión de legajos.');
          return;
        }

        const legajoId = btn.getAttribute('data-legajo-id');
        const accion = btn.getAttribute('data-accion'); // "APROBAR" | "RECHAZAR"
        if (!legajoId || !accion) return;

        const url = window.REVISAR_URL_TEMPLATE.replace('{id}', legajoId);

        const container = btn.closest('.legajo-item') || document;
        const btnAprobar = container.querySelector(`.btn-revision[data-legajo-id="${legajoId}"][data-accion="APROBAR"]`);
        const btnRechazar = container.querySelector(`.btn-revision[data-legajo-id="${legajoId}"][data-accion="RECHAZAR"]`);

        setLoading(btn, true);

        try {
          const fd = new FormData();
          fd.append('accion', accion);

          const resp = await fetch(url, {
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
            data = { success: true, estado: accion === 'APROBAR' ? 'APROBADO' : 'RECHAZADO' };
          }

          if (!resp.ok || data.success === false) {
            const msg = data.error || `HTTP ${resp.status}`;
            throw new Error(msg);
          }

          toggleActive(
            btnAprobar,
            btnRechazar,
            data.estado || (accion === 'APROBAR' ? 'APROBADO' : 'RECHAZADO'),
          );
          showAlert('success', 'Legajo ', legajoId, ': estado actualizado a ', data.estado, '.');

        } catch (err) {
          console.error('Revisión de legajo:', err);
          showAlert(
            'danger',
            'No se pudo actualizar el estado del legajo ',
            legajoId,
            '. ',
            err.message,
          );
        } finally {
          setLoading(btn, false);
        }
      });
    });
  })();

  /* ===== Inicializar paginación para PREVIEW ===== */
  (function initPreviewPagination() {
    const tbody = document.getElementById('preview-tbody');
    const pageSizeSel = document.getElementById('preview-page-size');
    const pagUl = document.getElementById('preview-pagination');

    if (!tbody || !pageSizeSel || !pagUl) {
      console.log('Elementos preview no encontrados');
      return;
    }

    // Skip if already fixed by pagination_fix.js
    if (pageSizeSel.hasAttribute('data-fixed')) {
      console.log('Preview pagination already fixed, skipping original implementation');
      return;
    }

    // Obtener todas las filas de preview y almacenar los datos
    const getAllPreviewRows = () => {
      return Array.from(tbody.querySelectorAll('.preview-row'));
    };

    let allItems = getAllPreviewRows();
    if (allItems.length === 0) {
      console.log('No hay filas preview para paginar');
      return;
    }

    // Almacenar los datos originales para evitar pérdida
    const originalData = allItems.map(row => ({
      element: row.cloneNode(true),
      html: row.outerHTML
    }));

    let currentPage = 1;

    function getCurrentPageSize() {
      const val = pageSizeSel.value;
      return val === 'all' ? originalData.length : parseInt(val, 10) || 10;
    }

    function renderPage() {
      const pageSize = getCurrentPageSize();
      const totalPages = Math.ceil(originalData.length / pageSize);

      if (currentPage > totalPages && totalPages > 0) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      console.log('Renderizando preview:', { 
        currentPage, 
        pageSize, 
        totalPages, 
        start, 
        end, 
        totalItems: originalData.length 
      });

      // Limpiar tbody y agregar solo las filas de la página actual
      tbody.innerHTML = '';
      
      for (let i = start; i < end && i < originalData.length; i++) {
        const clonedRow = originalData[i].element.cloneNode(true);
        // Mantener la clase preview-row para compatibilidad
        if (!clonedRow.classList.contains('preview-row')) {
          clonedRow.classList.add('preview-row');
        }
        tbody.appendChild(clonedRow);
      }

      // Generar paginación mejorada
      pagUl.innerHTML = '';

      if (totalPages > 1) {
        // Botón anterior
        const prevLi = document.createElement('li');
        prevLi.className = `page-item${currentPage === 1 ? ' disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Anterior">&laquo;</a>`;
        if (currentPage > 1) {
          prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage--;
            renderPage();
          });
        }
        pagUl.appendChild(prevLi);

        // Páginas numeradas (mostrar máximo 5 páginas)
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        if (endPage - startPage < 4) {
          startPage = Math.max(1, endPage - 4);
        }

        // Primera página si no está visible
        if (startPage > 1) {
          const firstLi = document.createElement('li');
          firstLi.className = 'page-item';
          firstLi.innerHTML = '<a class="page-link" href="#">1</a>';
          firstLi.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = 1;
            renderPage();
          });
          pagUl.appendChild(firstLi);

          if (startPage > 2) {
            const dotsLi = document.createElement('li');
            dotsLi.className = 'page-item disabled';
            dotsLi.innerHTML = '<span class="page-link">...</span>';
            pagUl.appendChild(dotsLi);
          }
        }

        // Páginas del rango visible
        for (let i = startPage; i <= endPage; i++) {
          const li = document.createElement('li');
          li.className = `page-item${i === currentPage ? ' active' : ''}`;
          li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
          li.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = i;
            renderPage();
          });
          pagUl.appendChild(li);
        }

        // Última página si no está visible
        if (endPage < totalPages) {
          if (endPage < totalPages - 1) {
            const dotsLi = document.createElement('li');
            dotsLi.className = 'page-item disabled';
            dotsLi.innerHTML = '<span class="page-link">...</span>';
            pagUl.appendChild(dotsLi);
          }
          
          const lastLi = document.createElement('li');
          lastLi.className = 'page-item';
          lastLi.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
          lastLi.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage = totalPages;
            renderPage();
          });
          pagUl.appendChild(lastLi);
        }

        // Botón siguiente
        const nextLi = document.createElement('li');
        nextLi.className = `page-item${currentPage === totalPages ? ' disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Siguiente">&raquo;</a>`;
        if (currentPage < totalPages) {
          nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            currentPage++;
            renderPage();
          });
        }
        pagUl.appendChild(nextLi);
      }
    }

    pageSizeSel.addEventListener('change', function () {
      console.log('Selector de preview cambió a:', this.value);
      currentPage = 1;
      renderPage();
    });

    // Renderizar página inicial
    renderPage();
  })();

  // ===== CONFIRMAR ENVÍO =====
  const btnConfirm = document.getElementById('btn-confirm');
  if (btnConfirm) {
    btnConfirm.addEventListener('click', async () => {
      // Verificar si el botón está deshabilitado
      if (btnConfirm.disabled) {
        showAlert('warning', 'No se puede confirmar el envío mientras haya registros con errores pendientes.');
        return;
      }

      const original = btnConfirm.innerHTML;
      btnConfirm.disabled = true;
      btnConfirm.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando…';

      try {
        if (!window.CONFIRM_URL) throw new Error('No se configuró CONFIRM_URL.');

        const resp = await fetch(window.CONFIRM_URL, {
          method: 'POST',
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
          const msg = data.error || data.message || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        showAlert('success', data.message || 'Envío confirmado.');
      } catch (err) {
        console.error('Confirmar envío:', err);
        showAlert('danger', 'No se pudo confirmar el envío. ', err.message);
      } finally {
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = original;
        window.location.reload();
      }
    });
  }

  // ===== CONFIRMAR SUBSANACIÓN =====
  const btnConfirmSubs = document.getElementById('btn-confirm-subs');
  if (btnConfirmSubs) {
    const zone = ensureAlertsZone();
    btnConfirmSubs.addEventListener('click', async () => {
      if (!window.CONFIRM_SUBS_URL) {
        showAlert('danger', 'No se configuró la URL de Confirmar Subsanación.');
        return;
      }
      const original = btnConfirmSubs.innerHTML;
      btnConfirmSubs.disabled = true;
      btnConfirmSubs.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando…';

      try {
        const resp = await fetch(window.CONFIRM_SUBS_URL, {
          method: 'POST',
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
          throw new Error(data.error || data.message || `HTTP ${resp.status}`);
        }

        showAlert('success', data.message || 'Subsanación confirmada.');
        setTimeout(() => window.location.reload(), 800);

      } catch (err) {
        showAlert('danger', 'No se pudo confirmar la subsanación. ', err.message);
        btnConfirmSubs.disabled = false;
        btnConfirmSubs.innerHTML = original;
      }
    });
  }



  /* ===== VALIDACIÓN RENAPER ===== */

  // Función para mostrar modal de subsanación Renaper
  function mostrarModalSubsanarRenaper(legajoId, modalRenaper) {
    const modalHtml = `
      <div class="modal fade" id="modalSubsanarRenaper" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Subsanar Validación Renaper</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label for="comentario-subsanar-renaper" class="form-label">Comentario de subsanación</label>
                <textarea id="comentario-subsanar-renaper" class="form-control" rows="3" 
                          placeholder="Indique qué datos necesitan ser corregidos..." required></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
              <button type="button" class="btn btn-warning" id="btn-confirmar-subsanar-renaper">Confirmar Subsanación</button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Eliminar modal anterior si existe
    const modalExistente = document.getElementById('modalSubsanarRenaper');
    if (modalExistente) modalExistente.remove();

    // Agregar nuevo modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modalSubsanar = new bootstrap.Modal(document.getElementById('modalSubsanarRenaper'));
    modalSubsanar.show();

    // Event listener para confirmar
    document.getElementById('btn-confirmar-subsanar-renaper').addEventListener('click', async () => {
      const comentario = document.getElementById('comentario-subsanar-renaper').value.trim();

      if (!comentario) {
        showAlert('warning', 'Debe ingresar un comentario de subsanación.');
        return;
      }

      await guardarValidacionRenaperConComentario(legajoId, '3', comentario);
      modalSubsanar.hide();
      modalRenaper.hide();
      setTimeout(() => window.location.reload(), 1000);
    });
  }

  // Función para guardar el estado de validación Renaper
  async function guardarValidacionRenaper(legajoId, estado, mensaje) {
    try {
      if (!window.VALIDAR_RENAPER_URL_TEMPLATE) {
        throw new Error('URL de validación no configurada');
      }

      const url = window.VALIDAR_RENAPER_URL_TEMPLATE.replace('{id}', legajoId);

      const formData = new FormData();
      formData.append('validacion_estado', estado);

      const resp = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      const data = await resp.json();

      if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Error al guardar validación');
      }

      showAlert('success', mensaje);

    } catch (err) {
      console.error('Error guardar validación Renaper:', err);
      showAlert('danger', 'Error al guardar validación: ' + err.message);
    }
  }

  // Función para guardar validación Renaper con comentario
  async function guardarValidacionRenaperConComentario(legajoId, estado, comentario) {
    try {
      if (!window.VALIDAR_RENAPER_URL_TEMPLATE) {
        throw new Error('URL de validación no configurada');
      }

      const url = window.VALIDAR_RENAPER_URL_TEMPLATE.replace('{id}', legajoId);

      const formData = new FormData();
      formData.append('validacion_estado', estado);
      formData.append('comentario', comentario);

      const resp = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      const data = await resp.json();

      if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Error al guardar validación');
      }

      showAlert('success', 'Subsanación Renaper guardada correctamente.');

    } catch (err) {
      console.error('Error guardar subsanación Renaper:', err);
      showAlert('danger', 'Error al guardar subsanación: ' + err.message);
    }
  }

  const modalValidarRenaper = document.getElementById('modalValidarRenaper');
  if (modalValidarRenaper) {
    // Limpiar backdrop cuando se cierra el modal
    modalValidarRenaper.addEventListener('hidden.bs.modal', function () {
      const backdrops = document.querySelectorAll('.modal-backdrop');
      backdrops.forEach(backdrop => backdrop.remove());
      document.body.classList.remove('modal-open');
      document.body.style.removeProperty('overflow');
      document.body.style.removeProperty('padding-right');
    });

    const btnValidarRenaper = document.querySelectorAll('.btn-validar-renaper');

    btnValidarRenaper.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();

        const legajoId = btn.getAttribute('data-legajo-id');
        if (!legajoId || !window.VALIDAR_RENAPER_URL_TEMPLATE) {
          showAlert('danger', 'Error de configuración para validación Renaper.');
          return;
        }

        const url = window.VALIDAR_RENAPER_URL_TEMPLATE.replace('{id}', legajoId);

        // Mostrar modal y loading
        const modal = new bootstrap.Modal(modalValidarRenaper);
        modal.show();

        const loadingDiv = document.getElementById('renaper-loading');
        const comparacionDiv = document.getElementById('renaper-comparacion');
        const alertasDiv = document.getElementById('renaper-alertas');

        loadingDiv.style.display = 'block';
        comparacionDiv.style.display = 'none';
        alertasDiv.innerHTML = '';

        try {
          const resp = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'X-CSRFToken': getCsrfToken(),
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/json'
            }
          });

          const responseText = await resp.text();
          console.log('=== RESPUESTA COMPLETA DEL SERVIDOR ===');
          console.log('Status:', resp.status);
          console.log('Headers:', Object.fromEntries(resp.headers.entries()));
          console.log('Body:', responseText);
          console.log('=======================================');

          let data;
          try {
            data = JSON.parse(responseText);
          } catch (parseError) {
            console.error('ERROR AL PARSEAR JSON:', parseError);
            console.error('Respuesta del servidor:', responseText);
            throw new Error(`Error del servidor (${resp.status}): ${responseText.substring(0, 200)}`);
          }

          if (!resp.ok || !data.success) {
            throw new Error(data.error || 'Error al consultar Renaper');
          }

          // Mostrar comparación
          loadingDiv.style.display = 'none';
          comparacionDiv.style.display = 'block';

          document.getElementById('ciudadano-nombre').textContent = data.ciudadano_nombre;

          // Llenar datos provincia
          const datosProvinciaTable = document.getElementById('datos-provincia');
          datosProvinciaTable.innerHTML = '';

          const campos = [
            { key: 'documento', label: 'DNI' },
            { key: 'nombre', label: 'Nombre' },
            { key: 'apellido', label: 'Apellido' },
            { key: 'fecha_nacimiento', label: 'Fecha Nacimiento' },
            { key: 'sexo', label: 'Sexo' },
            { key: 'calle', label: 'Calle' },
            { key: 'altura', label: 'Altura' },
            { key: 'piso_departamento', label: 'Piso/Depto' },
            { key: 'ciudad', label: 'Ciudad' },
            { key: 'provincia', label: 'Provincia' },
            { key: 'codigo_postal', label: 'Código Postal' }
          ];

          campos.forEach(campo => {
            const valorProvincia = data.datos_provincia[campo.key] || '-';
            const valorRenaper = data.datos_renaper[campo.key] || '-';

            const coincide = valorProvincia === valorRenaper;
            const claseCoincidencia = coincide ? 'table-success' : 'table-warning';

            const rowProvincia = document.createElement('tr');
            rowProvincia.className = claseCoincidencia;
            rowProvincia.innerHTML = `
              <td><strong>${campo.label}</strong></td>
              <td>${escapeHtml(valorProvincia)}</td>
            `;
            datosProvinciaTable.appendChild(rowProvincia);
          });

          // Llenar datos Renaper
          const datosRenaperTable = document.getElementById('datos-renaper');
          datosRenaperTable.innerHTML = '';

          campos.forEach(campo => {
            const valorProvincia = data.datos_provincia[campo.key] || '-';
            const valorRenaper = data.datos_renaper[campo.key] || '-';

            const coincide = valorProvincia === valorRenaper;
            const claseCoincidencia = coincide ? 'table-success' : 'table-warning';

            const rowRenaper = document.createElement('tr');
            rowRenaper.className = claseCoincidencia;
            rowRenaper.innerHTML = `
              <td><strong>${campo.label}</strong></td>
              <td>${escapeHtml(valorRenaper)}</td>
            `;
            datosRenaperTable.appendChild(rowRenaper);
          });

          // Limpiar botones anteriores si existen
          const botonesExistentes = comparacionDiv.querySelector('.mt-3.text-center');
          if (botonesExistentes) {
            botonesExistentes.remove();
          }

          // Mostrar botones para validación de Renaper
          const botonesDiv = document.createElement('div');
          botonesDiv.className = 'mt-3 text-center';
          botonesDiv.innerHTML = `
            <h6>Validación de Renaper completada. ¿Los datos coinciden?</h6>
            <div class="btn-group" role="group">
              <button type="button" class="btn btn-success btn-aprobar-renaper">✅ Datos correctos</button>
              <button type="button" class="btn btn-danger btn-rechazar-renaper">❌ Datos incorrectos</button>
              <button type="button" class="btn btn-warning btn-subsanar-renaper">📝 Subsanar</button>
            </div>
            <p class="small text-muted mt-2">Esto solo valida la información de Renaper. Luego podrás aprobar/rechazar todo el legajo.</p>
          `;

          comparacionDiv.appendChild(botonesDiv);

          // Agregar event listeners para validación de Renaper
          const legajoId = btn.getAttribute('data-legajo-id');

          botonesDiv.querySelector('.btn-aprobar-renaper').addEventListener('click', async () => {
            await guardarValidacionRenaper(legajoId, '1', 'Datos aceptados. Ahora puedes revisar el legajo completo.');
            modal.hide();
            setTimeout(() => window.location.reload(), 1000);
          });

          botonesDiv.querySelector('.btn-rechazar-renaper').addEventListener('click', async () => {
            await guardarValidacionRenaper(legajoId, '2', 'Datos rechazados. El legajo no se puede revisar hasta corregir los datos.');
            modal.hide();
            setTimeout(() => window.location.reload(), 1000);
          });

          botonesDiv.querySelector('.btn-subsanar-renaper').addEventListener('click', () => {
            mostrarModalSubsanarRenaper(legajoId, modal);
          });

        } catch (err) {
          console.error('Error validación Renaper:', err);
          loadingDiv.style.display = 'none';
          alertasDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
              Error validación Renaper: ${escapeHtml(err.message)}
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
          `;
        }
      });
    });
  }

  /* ===== MODAL RESPUESTA SUBSANACIÓN RENAPER ===== */
  const modalRespuestaRenaper = document.getElementById('modalRespuestaSubsanacionRenaper');
  if (modalRespuestaRenaper) {
    const formRespuesta = modalRespuestaRenaper.querySelector('#form-respuesta-subsanacion-renaper');
    if (!formRespuesta) {
      console.error('No se encontró el formulario de respuesta Renaper dentro del modal.');
      return;
    }

    const renderModalAlert = (type, message) => {
      const alertasNode = modalRespuestaRenaper.querySelector('#modal-alertas-renaper');
      if (!alertasNode) return;
      alertasNode.innerHTML = `
        <div class="alert alert-${escapeHtml(type)} alert-dismissible fade show" role="alert">
          ${escapeHtml(message)}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;
    };

    modalRespuestaRenaper.addEventListener('show.bs.modal', (event) => {
      const button = event.relatedTarget;
      const legajoId = button ? button.getAttribute('data-legajo-id') : null;
      const expedienteId = button ? button.getAttribute('data-expediente-id') : null;
      const alertas = modalRespuestaRenaper.querySelector('#modal-alertas-renaper');
      if (alertas) alertas.innerHTML = '';

      if (!legajoId || !expedienteId) {
        console.error('Modal Respuesta Renaper abierto sin IDs requeridos.', { legajoId, expedienteId, button });
        formRespuesta.removeAttribute('action');
        delete modalRespuestaRenaper.dataset.actionUrl;
        renderModalAlert('danger', 'No se pudo preparar el formulario porque faltan datos del legajo.');
        return;
      }

      const actionUrl = `/expedientes/${expedienteId}/ciudadanos/${legajoId}/respuesta-subsanacion-renaper/`;
      formRespuesta.setAttribute('action', actionUrl);
      modalRespuestaRenaper.dataset.actionUrl = actionUrl;

      // Limpiar campos
      const comentarioInput = document.getElementById('comentario-respuesta-renaper');
      const archivoInput = document.getElementById('archivo-respuesta-renaper');
      if (comentarioInput) comentarioInput.value = '';
      if (archivoInput) archivoInput.value = '';
    });

    formRespuesta.addEventListener('submit', async (e) => {
      e.preventDefault();

      const comentarioInput = document.getElementById('comentario-respuesta-renaper');
      const comentario = comentarioInput ? comentarioInput.value.trim() : '';
      const alertas = modalRespuestaRenaper.querySelector('#modal-alertas-renaper');
      if (alertas) alertas.innerHTML = '';
      if (!comentario) {
        showAlert('warning', 'Debe ingresar un comentario de respuesta.');
        renderModalAlert('warning', 'Debe ingresar un comentario de respuesta.');
        return;
      }

      const btnSubmit = formRespuesta.querySelector('button[type="submit"]');
      if (!btnSubmit) {
        console.error('No se encontró el botón de envío en el formulario de respuesta Renaper.');
        renderModalAlert('danger', 'No se pudo enviar la respuesta por un error de configuración.');
        return;
      }

      const url = formRespuesta.getAttribute('action') || modalRespuestaRenaper.dataset.actionUrl;
      if (!url) {
        console.error('Intento de envío de respuesta Renaper sin URL configurada.');
        renderModalAlert('danger', 'No se pudo determinar la URL para enviar la respuesta. Cerrá el modal e intentá nuevamente.');
        return;
      }

      const formData = new FormData(formRespuesta);
      const originalHTML = btnSubmit.innerHTML;

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando...';

      try {
        console.log('=== ENVIANDO RESPUESTA RENAPER ===');
        console.log('URL:', url);
        console.log('FormData entries:');
        for (let pair of formData.entries()) {
          console.log(pair[0], ':', pair[1]);
        }
        console.log('==================================');

        const resp = await fetch(url, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        console.log('=== RESPUESTA RECIBIDA ===');
        console.log('Status:', resp.status);
        console.log('OK:', resp.ok);
        console.log('==========================');

        const responseText = await resp.text();
        console.log('Response text:', responseText);

        let data;
        try {
          data = JSON.parse(responseText);
        } catch (e) {
          console.error('Error parseando JSON:', e);
          throw new Error('Respuesta inválida del servidor: ' + responseText.substring(0, 200));
        }

        console.log('Data parseada:', data);

        if (!resp.ok || !data.success) {
          const errorMsg = data.error || data.message || data.detail || 
                          (data.non_field_errors && data.non_field_errors[0]) ||
                          (data.errors && JSON.stringify(data.errors)) ||
                          responseText.substring(0, 200) ||
                          'Error al enviar respuesta';
          throw new Error(errorMsg);
        }

        renderModalAlert('success', data.message || 'Respuesta enviada correctamente.');

        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalRespuestaRenaper);
          modal.hide();
          window.location.reload();
        }, 800);

      } catch (err) {
        console.error('=== ERROR COMPLETO ===');
        console.error('Error:', err);
        console.error('Message:', err.message);
        console.error('Stack:', err.stack);
        console.error('=====================');
        renderModalAlert('danger', err.message || 'Error al enviar respuesta');
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalHTML;
      }
    });
  }

  // El filtro por estado ahora se maneja dentro de la paginación de legajos
  // para evitar conflictos y mantener la consistencia de datos


});

  /* ===== CONFIRMAR SUBSANACIÓN INDIVIDUAL ===== */
  const botonesConfirmarSubsanacion = document.querySelectorAll('.btn-confirmar-subsanacion-individual');
  botonesConfirmarSubsanacion.forEach(btn => {
    btn.addEventListener('click', async () => {
      const legajoId = btn.getAttribute('data-legajo-id');
      const expedienteId = btn.getAttribute('data-expediente-id');
      
      if (!legajoId || !expedienteId) {
        showAlert('danger', 'Error: No se pudo identificar el legajo.');
        return;
      }

      if (!window.CONFIRM_SUBS_URL) {
        showAlert('danger', 'Error: URL de confirmación no configurada.');
        return;
      }

      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Confirmando...';

      try {
        const url = window.CONFIRM_SUBS_URL;
        const formData = new FormData();
        formData.append('legajo_id', legajoId);

        const resp = await fetch(url, {
          method: 'POST',
          body: formData,
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
          throw new Error(data.error || data.message || `HTTP ${resp.status}`);
        }

        showAlert('success', data.message || 'Subsanación confirmada correctamente.');
        setTimeout(() => window.location.reload(), 800);

      } catch (err) {
        console.error('Error confirmar subsanación:', err);
        showAlert('danger', 'Error al confirmar subsanación: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = original;
      }
    });
  });

  /* ===== PAGINACIÓN DE LEGAJOS DESACTIVADA ===== */
  setTimeout(() => {
    const pageSizeSel = document.getElementById('legajos-page-size');
    const pagUl = document.getElementById('legajos-pagination');
    
    // Ocultar completamente los controles de paginaci��n
    if (pageSizeSel) {
      pageSizeSel.style.display = 'none';
    }
    if (pagUl) {
      pagUl.style.display = 'none';
    }
    
    return; // Salir sin hacer nada más


  }, 100);

  /* ===== BUSCADOR DE LEGAJOS ===== */
  const searchInput = document.getElementById('search-legajos');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase().trim();
      const rows = document.querySelectorAll('.legajo-row');
      
      rows.forEach(function(row) {
        const searchData = row.getAttribute('data-search') || '';
        const isVisible = searchData.includes(searchTerm);
        
        // Mostrar/ocultar fila principal
        row.style.display = isVisible ? '' : 'none';
        
        // También ocultar la fila de detalle expandible si existe
        const nextRow = row.nextElementSibling;
        if (nextRow && nextRow.classList.contains('collapse')) {
          nextRow.style.display = isVisible ? '' : 'none';
        }
      });
    });
  }

  /* ===== EDITAR LEGAJO ===== */
  const modalEditarLegajo = document.getElementById('modalEditarLegajo');
  if (modalEditarLegajo) {
    modalEditarLegajo.addEventListener('show.bs.modal', async function(event) {
      const button = event.relatedTarget;
      const legajoId = button.getAttribute('data-legajo-id');
      const expedienteId = button.getAttribute('data-expediente-id');
      
      if (!legajoId || !expedienteId) {
        console.error('Faltan datos del legajo');
        return;
      }
      
      try {
        // Cargar datos actuales del legajo
        const editarLegajoMeta = document.querySelector('meta[name="editar-legajo-url-template"]');
        const editarLegajoUrlTemplate = editarLegajoMeta?.getAttribute('content')?.replace('/0/', '/{id}/');
        if (!editarLegajoUrlTemplate) {
          showAlert('danger', 'URL de edición no configurada.');
          return;
        }
        const editarUrl = editarLegajoUrlTemplate.replace('{id}', legajoId);
        
        const response = await fetch(editarUrl, {
          method: 'GET',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          const legajo = data.legajo;
          
          // Llenar el formulario con los datos actuales
          document.getElementById('editar-apellido').value = legajo.apellido;
          document.getElementById('editar-nombre').value = legajo.nombre;
          document.getElementById('editar-documento').value = legajo.documento;
          document.getElementById('editar-fecha-nacimiento').value = legajo.fecha_nacimiento;
          document.getElementById('editar-sexo').value = legajo.sexo || '';
          document.getElementById('editar-nacionalidad').value = legajo.nacionalidad || '';
          document.getElementById('editar-telefono').value = legajo.telefono;
          document.getElementById('editar-email').value = legajo.email;
          document.getElementById('editar-calle').value = legajo.calle;
          document.getElementById('editar-altura').value = legajo.altura;
          document.getElementById('editar-codigo-postal').value = legajo.codigo_postal;
          
          // Configurar la acción del formulario
          const form = document.getElementById('form-editar-legajo');
          form.setAttribute('action', editarUrl);
        } else {
          showAlert('danger', 'Error al cargar los datos: ' + data.error);
        }
      } catch (error) {
        console.error('Error cargando datos del legajo:', error);
        showAlert('danger', 'Error al cargar los datos del legajo.');
      }
    });
    
    // Manejar envío del formulario
    const formEditarLegajo = document.getElementById('form-editar-legajo');
    if (formEditarLegajo) {
      formEditarLegajo.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        const alertasDiv = document.getElementById('modal-alertas-editar');
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
        alertasDiv.innerHTML = '';
        
        try {
          const formData = new FormData(this);
          const response = await fetch(this.getAttribute('action'), {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
              'X-CSRFToken': getCsrfToken(),
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/json'
            }
          });
          
          const data = await response.json();
          
          if (data.success) {
            showAlert('success', data.message);
            const modal = bootstrap.Modal.getInstance(modalEditarLegajo);
            modal.hide();
            setTimeout(() => window.location.reload(), 1000);
          } else {
            alertasDiv.innerHTML = `
              <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${data.error}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
              </div>
            `;
          }
        } catch (error) {
          console.error('Error guardando cambios:', error);
          alertasDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
              Error al guardar los cambios.
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
          `;
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      });
    }
  }

  /* ===== ELIMINAR LEGAJO ===== */
  const botonesEliminar = document.querySelectorAll('.btn-eliminar-legajo');
  botonesEliminar.forEach(btn => {
    btn.addEventListener('click', async () => {
      const legajoId = btn.getAttribute('data-legajo-id');
      
      if (!legajoId) {
        showAlert('danger', 'Error: No se pudo identificar el legajo.');
        return;
      }

      if (!window.REVISAR_URL_TEMPLATE) {
        showAlert('danger', 'No se configuró la URL de revisión de legajos.');
        return;
      }

      const url = window.REVISAR_URL_TEMPLATE.replace('{id}', legajoId);

      let previewMsg = '¿Estás seguro de que querés dar de baja este legajo?';
      try {
        const previewFd = new FormData();
        previewFd.append('accion', 'ELIMINAR');
        previewFd.append('preview', '1');
        const previewResp = await fetch(url, {
          method: 'POST',
          body: previewFd,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        });
        const previewData = await previewResp.json();
        if (previewResp.ok && previewData.success && previewData.preview) {
          const desglose = (previewData.preview.desglose_por_modelo || [])
            .map((item) => `- ${item.modelo}: ${item.cantidad}`)
            .join('\n');
          previewMsg = `Se aplicará baja lógica en cascada.\nTotal afectados: ${previewData.preview.total_afectados}\n${desglose}`;
        }
      } catch (error) {
        console.warn('No se pudo obtener preview de eliminación:', error);
      }

      if (!confirm(previewMsg)) {
        return;
      }

      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

      try {
        const fd = new FormData();
        fd.append('accion', 'ELIMINAR');
        
        const resp = await fetch(url, {
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
          const msg = data.error || data.message || `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        showAlert('success', data.message || 'Legajo eliminado correctamente.');
        setTimeout(() => window.location.reload(), 800);

      } catch (err) {
        console.error('Error eliminar legajo:', err);
        showAlert('danger', 'Error al eliminar legajo: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = original;
      }
    });
  });

// Buscador de legajos
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-legajos');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.legajo-row');
            
            rows.forEach(function(row) {
                const searchData = row.getAttribute('data-search') || '';
                const isVisible = searchData.includes(searchTerm);
                
                // Mostrar/ocultar fila principal
                row.style.display = isVisible ? '' : 'none';
                
                // También ocultar la fila de detalle expandible si existe
                const nextRow = row.nextElementSibling;
                if (nextRow && nextRow.classList.contains('collapse')) {
                    nextRow.style.display = isVisible ? '' : 'none';
                }
            });
        });
    }
});
