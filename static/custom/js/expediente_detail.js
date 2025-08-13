/* static/custom/js/expediente_detail.js
 * - Procesar expediente
 * - Subir/editar archivo de legajo
 * - Confirmar Envío
 */

document.addEventListener('DOMContentLoaded', () => {
  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return m ? m[2] : null;
  }
  function getCsrfToken() {
    // Prioriza el token inyectado desde Django. Si no, cae al cookie.
    return (typeof window !== 'undefined' && window.CSRF_TOKEN) || getCookie('csrftoken');
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

  /* ===== CONFIRMAR ENVÍO (EN_ESPERA → CONFIRMACION_DE_ENVIO) ===== */
  const btnConfirm = document.getElementById('btn-confirm');
  if (btnConfirm) {
    let alertZone = document.getElementById('expediente-alerts');
    if (!alertZone) {
      alertZone = document.createElement('div');
      alertZone.id = 'expediente-alerts';
      const headerBlock = document.querySelector('.p-3.rounded.shadow.mb-4');
      (headerBlock || document.body).prepend(alertZone);
    }

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
});
