/* static/custom/js/expediente_detail.js
 * - Procesar expediente
 * - Subir/editar archivo de legajo
 * - Confirmar Envío
 * - Subir/Reprocesar Excel de CUITs y ejecutar cruce (técnico)
 */

document.addEventListener('DOMContentLoaded', () => {
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
        // Backend espera "excel_cuit" o "archivo"? — usamos "archivo" porque tu view lee request.FILES["archivo"]
        fd.delete('excel_cuit'); // por si quedó
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
});
