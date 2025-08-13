/* static/custom/js/celiaquia_list.js
 * -------------------------------------------------------------------------
 * Breve descripción:
 *   Acciones inline desde la lista de Expedientes según rol:
 *   - Provincia: Procesar (CREADO) y Confirmar Envío (EN_ESPERA).
 *   - Coordinador: Recepcionar (CONFIRMACION_DE_ENVIO).
 *
 * Estados y flujos impactados:
 *   CREADO → (procesar) → PROCESADO → EN_ESPERA
 *   EN_ESPERA → (confirmar) → CONFIRMACION_DE_ENVIO
 *   CONFIRMACION_DE_ENVIO → (recepcionar) → (sin cambio de estado; asignación pone ASIGNADO)
 *
 * Dependencias:
 *   - Plantilla 'celiaquia/expediente_list.html' inyecta window.CSRF_TOKEN.
 *   - Rutas:
 *       name='expediente_procesar'        (POST)
 *       name='expediente_confirm'         (POST)
 *       name='expediente_recepcionar'     (POST)
 *   - Botones con data-atributos:
 *       .js-process       data-process-url="..."
 *       .js-confirm       data-confirm-url="..."
 *       .js-recepcionar   data-recepcionar-url="..."
 *   - Bootstrap (alertas y estilos)
 * -------------------------------------------------------------------------
 */

(function () {
  // ---------- Utils ----------
  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return m ? m[2] : null;
  }
  function csrfToken() {
    return (typeof window !== 'undefined' && window.CSRF_TOKEN) || getCookie('csrftoken');
  }
  function alertsZone() {
    let zone = document.getElementById('list-alerts');
    if (!zone) {
      zone = document.createElement('div');
      zone.id = 'list-alerts';
      const container = document.querySelector('.card.shadow-sm') || document.body;
      container.parentNode.insertBefore(zone, container);
    }
    return zone;
  }
  function showAlert(type, message) {
    const zone = alertsZone();
    zone.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>`;
  }

  async function postJson(url) {
    const resp = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': csrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      }
    });

    // Intentamos JSON; si no, devolvemos texto
    const ct = resp.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) {
      const data = await resp.json();
      return { ok: resp.ok, data, text: null, status: resp.status };
    }
    const text = await resp.text();
    return { ok: resp.ok, data: null, text, status: resp.status };
  }

  function withSpinner(btn, loadingText, fn) {
    return async function () {
      if (!btn) return;
      btn.disabled = true;
      const originalHTML = btn.innerHTML;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> ${loadingText}`;
      try {
        await fn();
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    };
  }

  function delegate(container, selector, type, handler) {
    container.addEventListener(type, function (e) {
      const target = e.target.closest(selector);
      if (target && container.contains(target)) {
        handler(e, target);
      }
    });
  }

  // ---------- Handlers por acción ----------
  function attachProcessHandlers() {
    const table = document.querySelector('table');
    if (!table) return;

    delegate(table, '.js-process', 'click', (e, btn) => {
      const url = btn.getAttribute('data-process-url');
      if (!url) {
        showAlert('danger', 'No se configuró la URL de procesamiento.');
        return;
      }
      withSpinner(btn, 'Procesando…', async () => {
        try {
          const { ok, data, text, status } = await postJson(url);
          if (!ok || (data && data.success === false)) {
            const msg = (data && data.error) || text || `HTTP ${status}`;
            throw new Error(msg);
          }
          const created = (data && data.creados) ?? 'los';
          const errs = (data && data.errores) ? ` (${data.errores} errores)` : '';
          showAlert('success', `Expediente procesado. Se crearon ${created} legajos.${errs} Pasó a <strong>EN ESPERA</strong>.`);
          setTimeout(() => window.location.reload(), 900);
        } catch (err) {
          console.error('Procesar expediente:', err);
          showAlert('danger', 'No se pudo procesar el expediente. ' + err.message);
        }
      })();
    });
  }

  function attachConfirmHandlers() {
    const table = document.querySelector('table');
    if (!table) return;

    delegate(table, '.js-confirm', 'click', (e, btn) => {
      const url = btn.getAttribute('data-confirm-url');
      if (!url) {
        showAlert('danger', 'No se configuró la URL de confirmación.');
        return;
      }
      withSpinner(btn, 'Enviando…', async () => {
        try {
          const { ok, data, text, status } = await postJson(url);
          if (!ok || (data && data.success === false)) {
            const msg = (data && data.error) || text || `HTTP ${status}`;
            throw new Error(msg);
          }
          const message = (data && data.message) || 'Expediente enviado a Subsecretaría.';
          showAlert('success', message);
          setTimeout(() => window.location.reload(), 800);
        } catch (err) {
          console.error('Confirmar envío:', err);
          showAlert('danger', 'No se pudo confirmar el envío. ' + err.message);
        }
      })();
    });
  }

  function attachRecepcionarHandlers() {
    const table = document.querySelector('table');
    if (!table) return;

    delegate(table, '.js-recepcionar', 'click', (e, btn) => {
      const url = btn.getAttribute('data-recepcionar-url');
      if (!url) {
        showAlert('danger', 'No se configuró la URL de recepción.');
        return;
      }
      withSpinner(btn, 'Recepcionando…', async () => {
        try {
          const { ok, data, text, status } = await postJson(url);
          if (!ok || (data && data.success === false)) {
            const msg = (data && data.error) || text || `HTTP ${status}`;
            throw new Error(msg);
          }
          showAlert('success', 'Expediente recepcionado. Ahora podés asignar un técnico.');
          setTimeout(() => window.location.reload(), 700);
        } catch (err) {
          console.error('Recepcionar expediente:', err);
          showAlert('danger', 'No se pudo recepcionar el expediente. ' + err.message);
        }
      })();
    });
  }

  // ---------- Init ----------
  document.addEventListener('DOMContentLoaded', () => {
    attachProcessHandlers();
    attachConfirmHandlers();
    attachRecepcionarHandlers();
  });
})();
