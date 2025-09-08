/* static/custom/js/celiaquia_list.js
 * -------------------------------------------------------------------------
 * Breve descripción:
 *   Acciones inline desde la lista de Expedientes según rol:
 *   - Provincia: Procesar (CREADO) y Confirmar Envío (EN_ESPERA).
 *   - Coordinador: Recepcionar (CONFIRMACION_DE_ENVIO -> RECEPCIONADO) y Asignar técnico (RECEPCIONADO|ASIGNADO -> ASIGNADO).
 *
 * Estados y flujos impactados:
 *   CREADO → (procesar) → PROCESADO → EN_ESPERA
 *   EN_ESPERA → (confirmar) → CONFIRMACION_DE_ENVIO
 *   CONFIRMACION_DE_ENVIO → (recepcionar) → RECEPCIONADO
 *   RECEPCIONADO|ASIGNADO → (asignar técnico) → ASIGNADO
 *
 * Dependencias:
 *   - Plantilla 'celiaquia/expediente_list.html' inyecta window.CSRF_TOKEN.
 *   - Rutas:
 *       name='expediente_procesar'        (POST)
 *       name='expediente_confirm'         (POST)
 *       name='expediente_recepcionar'     (POST)
 *       name='expediente_asignar_tecnico' (POST)
 *   - Botones con data-atributos:
 *       .js-process       data-process-url="..."
 *       .js-confirm       data-confirm-url="..."
 *       .js-recepcionar   data-recepcionar-url="..."
 *       .js-assign        data-assign-url="..."
 *   - Select del técnico en la fila (solo Coordinador):
 *       <select class="form-select form-select-sm js-tecnico" ... data-visible-when="recepcionado" class="d-none"></select>
 *   - Botón Asignar oculto hasta recepcionar:
 *       <button class="btn btn-sm btn-primary js-assign d-none" data-visible-when="recepcionado" ...>Asignar</button>
 *   - Bootstrap (alertas y estilos)
 * -------------------------------------------------------------------------
 */

// Added escapeHtml helper and sanitized alert messages to prevent HTML injection.

(function () {
  // ---------- Utils ----------
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/`/g, '&#96;');
  }
  if (typeof window !== 'undefined') {
    window.escapeHtml = escapeHtml;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports.escapeHtml = escapeHtml;
  }
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
    const safeMessage = escapeHtml(message);
    zone.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${safeMessage}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>`;
  }

  async function postJson(url, body=null) {
    const opts = {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': csrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      }
    };
    if (body && typeof body === 'object') {
      const params = new URLSearchParams();
      Object.entries(body).forEach(([k, v]) => params.append(k, v));
      opts.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
      opts.body = params.toString();
    }

    const resp = await fetch(url, opts);
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

  // ---------- Helpers de UI ----------
  function markRowRecepcionado(row) {
    // 1) Actualizar badge de estado (3ra columna)
    const estadoCell = row.querySelector('td:nth-child(3) .badge');
    if (estadoCell) {
      estadoCell.textContent = 'Recepcionado';
      estadoCell.className = estadoCell.className
        .replace(/\bbg-\w+\b/g, '')  // limpia cualquier bg-*
        .trim() + ' bg-secondary';
    }

    // 2) Ocultar botón "Recepcionar" de esa fila
    const recepBtn = row.querySelector('.js-recepcionar');
    if (recepBtn) recepBtn.classList.add('d-none');

    // 3) Mostrar selector y botón Asignar si ya están renderizados ocultos
    const revealables = row.querySelectorAll('[data-visible-when="recepcionado"].d-none');
    let revealed = false;
    revealables.forEach(el => {
      el.classList.remove('d-none');
      if (el.matches('select, button')) el.disabled = false;
      revealed = true;
    });

    return revealed; // si false, necesitaremos recargar
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
          showAlert(
            'success',
            `Expediente procesado. Se crearon ${created} legajos.${errs} Pasó a <strong>EN ESPERA</strong>.`
          );
        } catch (err) {
          console.error('Procesar expediente:', err);
          showAlert('danger', 'No se pudo procesar el expediente. ' + err.message);
        } finally {
          window.location.reload();
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
      const row = btn.closest('tr');

      withSpinner(btn, 'Recepcionando…', async () => {
        try {
          const { ok, data, text, status } = await postJson(url);
          if (!ok || (data && data.success === false)) {
            const msg = (data && data.error) || text || `HTTP ${status}`;
            throw new Error(msg);
          }

          // Intento actualizar la fila inline (si el template dejó los elementos ocultos)
          const didReveal = markRowRecepcionado(row);

          showAlert('success', 'Expediente recepcionado (estado: RECEPCIONADO). Ahora podés asignar un técnico.');
          if (!didReveal) {
            // Si no había elementos ocultos que revelar, recargamos para que el template los pinte
            setTimeout(() => window.location.reload(), 600);
          }
        } catch (err) {
          console.error('Recepcionar expediente:', err);
          showAlert('danger', 'No se pudo recepcionar el expediente. ' + err.message);
        }
      })();
    });
  }

  function attachAssignHandlers() {
    const table = document.querySelector('table');
    if (!table) return;

    delegate(table, '.js-assign', 'click', (e, btn) => {
      const url = btn.getAttribute('data-assign-url');
      if (!url) {
        showAlert('danger', 'No se configuró la URL de asignación.');
        return;
      }
      const row = btn.closest('tr');
      const select = row && row.querySelector('.js-tecnico');
      const tecnicoId = select && select.value;
      if (!tecnicoId) {
        showAlert('warning', 'Seleccioná un técnico antes de asignar.');
        return;
      }

      withSpinner(btn, 'Asignando…', async () => {
        try {
          const { ok, data, text, status } = await postJson(url, { tecnico_id: tecnicoId });
          if (!ok) {
            const msg = (data && data.error) || text || `HTTP ${status}`;
            throw new Error(msg);
          }
          showAlert('success', 'Técnico asignado correctamente. El expediente está en ASIGNADO.');
          // Actualizamos badge a ASIGNADO sin recargar
          const estadoCell = row.querySelector('td:nth-child(3) .badge');
          if (estadoCell) {
            estadoCell.textContent = 'Asignado';
            estadoCell.className = estadoCell.className.replace(/\bbg-\w+\b/g, '').trim() + ' bg-primary';
          }
        } catch (err) {
          console.error('Asignar técnico:', err);
          showAlert('danger', 'No se pudo asignar el técnico. ' + err.message);
        }
      })();
    });
  }

  // ---------- Init ----------
  document.addEventListener('DOMContentLoaded', () => {
    attachProcessHandlers();
    attachConfirmHandlers();
    attachRecepcionarHandlers();
    attachAssignHandlers();
  });
})();
