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
  /* ====== Paginación genérica client-side ====== */
  function paginate({
    items,
    pageSizeSelect,
    paginationUl,
    onPageChange,
    hideIfSinglePage = true,
  }) {
    const nodes = Array.from(items);
    console.log('Paginate called with:', { itemsCount: nodes.length, pageSizeSelect, paginationUl });
    
    if (!nodes.length || !pageSizeSelect || !paginationUl) {
      console.log('Paginate: missing required elements');
      return;
    }

    let page = 1;
    const readPageSize = () => {
      const val = pageSizeSelect.value;
      const size = val === 'all' ? Infinity : parseInt(val, 10) || 10;
      console.log('Page size:', val, '->', size);
      return size;
    };

    function render() {
      const pageSize = readPageSize();
      const total = nodes.length;
      const totalPages = pageSize === Infinity ? 1 : Math.max(1, Math.ceil(total / pageSize));
      if (page > totalPages) page = totalPages;

      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      nodes.forEach((el, i) => {
        el.style.display = (i >= start && i < end) ? '' : 'none';
      });

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
    btnProcess.addEventListener('click', async () => {
      btnProcess.disabled = true;
      let origHTML;
      try {
        origHTML = btnProcess.innerHTML;
        btnProcess.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...';

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

        const baseMsg =
          data.message ||
          `Se crearon ${data.creados ?? '-'} legajos y el expediente pasó a EN ESPERA.`;
        const errorExtra = data.errores ? ` ${data.errores} errores.` : '';
        showAlert('success', '¡Listo! ', baseMsg, errorExtra);

        setTimeout(() => window.location.reload(), 1000);
      } catch (err) {
        console.error('Error procesar expediente:', err);
        showAlert('danger', 'Error al procesar el expediente: ', err.message);
        btnProcess.innerHTML = origHTML;
        btnProcess.disabled = false;
      } finally {
        setTimeout(() => {
          btnProcess.innerHTML = origHTML;
          btnProcess.disabled = false;
        }, 1500);
      }
    });
  }

  /* ===== MODAL SUBIR/EDITAR ARCHIVO DE LEGAJO (archivo1/2/3) ===== */
  const modalArchivo = document.getElementById('modalSubirArchivo');
  if (modalArchivo) {
    modalArchivo.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const legajoId = button.getAttribute('data-legajo-id');
      const expedienteId = button.getAttribute('data-expediente-id');
      const defaultCampo = button?.getAttribute('data-file-field') || 'archivo1';
      const uploadForm = modalArchivo.querySelector('#form-subir-archivo');

      const actionUrl = `/expedientes/${expedienteId}/ciudadanos/${legajoId}/archivo/`;
      uploadForm.setAttribute('action', actionUrl);

      const selCampo = modalArchivo.querySelector('#campo-archivo');
      if (selCampo) selCampo.value = defaultCampo;

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
    const helpEl  = document.getElementById('cruce-help');
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
  (function initRevisionLegajos(){
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
        b.classList.remove('btn-success','btn-danger');
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
        const btnAprobar  = container.querySelector(`.btn-revision[data-legajo-id="${legajoId}"][data-accion="APROBAR"]`);
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

  // ===== CONFIRMAR ENVÍO =====
  const btnConfirm = document.getElementById('btn-confirm');
  if (btnConfirm) {
    btnConfirm.addEventListener('click', async () => {
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
    modalRespuestaRenaper.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const legajoId = button.getAttribute('data-legajo-id');
      const expedienteId = button.getAttribute('data-expediente-id');
      const form = modalRespuestaRenaper.querySelector('#form-respuesta-subsanacion-renaper');
      
      const actionUrl = `/expedientes/${expedienteId}/ciudadanos/${legajoId}/respuesta-subsanacion-renaper/`;
      form.setAttribute('action', actionUrl);
      
      const alertas = modalRespuestaRenaper.querySelector('#modal-alertas-renaper');
      if (alertas) alertas.innerHTML = '';
      
      // Limpiar campos
      document.getElementById('comentario-respuesta-renaper').value = '';
      document.getElementById('archivo-respuesta-renaper').value = '';
    });
    
    const formRespuesta = document.getElementById('form-respuesta-subsanacion-renaper');
    formRespuesta.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const comentario = document.getElementById('comentario-respuesta-renaper').value.trim();
      if (!comentario) {
        showAlert('warning', 'Debe ingresar un comentario de respuesta.');
        return;
      }
      
      const url = formRespuesta.getAttribute('action');
      const formData = new FormData(formRespuesta);
      const btnSubmit = formRespuesta.querySelector('button[type="submit"]');
      const originalHTML = btnSubmit.innerHTML;
      const alertas = modalRespuestaRenaper.querySelector('#modal-alertas-renaper');
      
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Enviando...';
      
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
        
        if (!resp.ok || !data.success) {
          throw new Error(data.message || 'Error al enviar respuesta');
        }
        
        alertas.innerHTML = `
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${data.message || 'Respuesta enviada correctamente.'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        
        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(modalRespuestaRenaper);
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
        console.error('Error al enviar respuesta:', err);
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalHTML;
      }
    });
  }
  
  /* ===== Inicializar paginación para LEGAJOS ===== */
  (function initLegajosPagination(){
    const list = document.getElementById('legajos-list');
    const pageSizeSel = document.getElementById('legajos-page-size');
    const pagUl = document.getElementById('legajos-pagination');
    
    console.log('Inicializando paginación legajos:', { list, pageSizeSel, pagUl });
    
    if (!list || !pageSizeSel || !pagUl) {
      console.log('Elementos no encontrados para paginación de legajos');
      return;
    }
    
    const items = list.querySelectorAll('.legajo-item');
    console.log('Items encontrados:', items.length);
    
    if (items.length === 0) {
      console.log('No hay items para paginar');
      return;
    }

    paginate({
      items: items,
      pageSizeSelect: pageSizeSel,
      paginationUl: pagUl,
      onPageChange: null,
    });
  })();
});
