// static/custom/js/informecabal.js
// [Informe Cabal - JS]
// - Modal de carga + previsualización AJAX paginada (25)
// - Procesamiento final del archivo
// - Reproceso por CÓDIGO de centro (pop-up) → POST JSON/URL-encoded
// - Mensajes Bootstrap (alertas)

(function () {
  // ---------- Helpers ----------
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  function showAlert(msg, type = 'warning') {
    if (!alertZone) return;
    const div = document.createElement('div');
    div.className = `alert alert-${type} fade show`;
    div.role = 'alert';
    div.innerHTML = msg;
    alertZone.innerHTML = '';
    alertZone.appendChild(div);
  }

  const CSRF_COOKIE_NAME = window.CSRF_COOKIE_NAME || 'csrftoken_v2';

  // ---------- Elements ----------
  const btnOpen = document.getElementById('btn-open-modal');
  const modalId = '#modalCabal';
  const fileInput = document.getElementById('fileCabal');
  const tableBody = document.querySelector('#preview-table tbody');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const pageIndicator = document.getElementById('page-indicator');
  const btnProcesar = document.getElementById('btn-procesar');
  const alertZone = document.getElementById('alert-zone');

  // Reproceso por código (pop-up)
  const btnReprocesar = document.getElementById('btn-reprocesar'); // botón que abre el modal
  const modalReprocesarEl = document.getElementById('modalReprocesarCentro');
  const inputCodigo = document.getElementById('codigoCentro');
  const btnConfirmReprocesar = document.getElementById('btnConfirmReprocesar');
  const outReprocess = document.getElementById('reprocess-result');
  const reprocessUrl = btnReprocesar ? btnReprocesar.dataset.url : null;

  // Si usás Bootstrap 5
  const BootstrapModal = window.bootstrap?.Modal;
  const modalReprocesar = (BootstrapModal && modalReprocesarEl)
    ? new BootstrapModal(modalReprocesarEl)
    : null;

  // ---------- State ----------
  let currentPage = 1;
  let totalRows = 0;
  let fileObj = null;

  // ---------- Tabla Preview ----------
  function clearTable() {
    if (!tableBody) return;
    tableBody.innerHTML = `<tr><td colspan="8" class="text-center">Sin datos</td></tr>`;
    totalRows = 0;
    currentPage = 1;
    if (pageIndicator) pageIndicator.textContent = '1';
    if (btnPrev) btnPrev.disabled = true;
    if (btnNext) btnNext.disabled = true;
    if (btnProcesar) btnProcesar.disabled = true;
  }

  function renderRows(rows) {
    if (!tableBody) return;
    if (!rows || !rows.length) {
      clearTable();
      return;
    }
    tableBody.innerHTML = '';
    rows.forEach(r => {
      const d = r.data || {};
      const tr = document.createElement('tr');
      if (r.no_coincidente) tr.classList.add('table-warning');
      tr.innerHTML = `
        <td>${r.fila ?? ''}</td>
        <td>${d.NroComercio ?? ''}</td>
        <td>${d.RazonSocial ?? ''}</td>
        <td>${d.Importe ?? ''}</td>
        <td>${d.FechaTRX ?? ''}</td>
        <td>${d.MonedaOrigen ?? ''}</td>
        <td>${d.ImportePesos ?? ''}</td>
        <td>${d.MotivoRechazo ?? ''}</td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function updatePager() {
    const totalPages = Math.ceil((totalRows || 0) / 25);
    if (pageIndicator) pageIndicator.textContent = String(currentPage);
    if (btnPrev) btnPrev.disabled = currentPage <= 1;
    if (btnNext) btnNext.disabled = currentPage >= totalPages || totalPages <= 1;
  }

  function fetchPreview(page = 1) {
    if (!fileObj || !window.urls?.informecabal_preview) return;
    const form = new FormData();
    form.append('file', fileObj);
    form.append('page', String(page));

    if (btnProcesar) btnProcesar.disabled = true;

    fetch(window.urls.informecabal_preview, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': window.csrfToken || getCookie(CSRF_COOKIE_NAME) },
      body: form
    })
      .then(r => r.json())
      .then(j => {
        if (!j.ok) {
          showAlert(j.error || 'Error al previsualizar', 'danger');
          clearTable();
          return;
        }
        totalRows = j.total || 0;
        renderRows(j.rows);
        if (btnProcesar) btnProcesar.disabled = false;
        updatePager();

        if (j.not_matching && j.not_matching.length) {
          showAlert(`Registros no coincidentes: (${j.not_matching.join(', ')})`, 'warning');
        } else if (alertZone) {
          alertZone.innerHTML = '';
        }
      })
      .catch(() => {
        showAlert('Error inesperado al previsualizar', 'danger');
        clearTable();
      });
  }

  // ---------- Procesar Archivo ----------
  function processFile(force = false) {
    if (!fileObj || !window.urls?.informecabal_process) return;
    const form = new FormData();
    form.append('file', fileObj);
    form.append('force', force ? 'true' : 'false');

    const spinner = document.getElementById('spin-procesar');
    if (spinner) spinner.classList.remove('d-none');
    if (btnProcesar) btnProcesar.disabled = true;

    fetch(window.urls.informecabal_process, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': window.csrfToken || getCookie(CSRF_COOKIE_NAME) },
      body: form
    })
      .then(r => r.json().then(j => ({ status: r.status, body: j })))
      .then(({ status, body }) => {
        if (spinner) spinner.classList.add('d-none');
        if (body.ok) {
          showAlert(
            `Archivo procesado. Total: ${body.total}, Válidas: ${body.validas}, Inválidas: ${body.invalidas}`,
            'success'
          );
          if (btnProcesar) btnProcesar.disabled = true;
          setTimeout(() => window.location.reload(), 800);
          return;
        }
        if (status === 409 && body.duplicate_name) {
          if (confirm('Ya se subió un archivo con este nombre. ¿Desea proseguir?')) {
            processFile(true);
          } else if (btnProcesar) {
            btnProcesar.disabled = false;
          }
          return;
        }
        showAlert(body.error || 'Error al procesar', 'danger');
        if (btnProcesar) btnProcesar.disabled = false;
      })
      .catch(() => {
        if (spinner) spinner.classList.add('d-none');
        showAlert('Error inesperado al procesar', 'danger');
        if (btnProcesar) btnProcesar.disabled = false;
      });
  }

  // ---------- Eventos: Modal de carga / Preview / Paginación / Proceso ----------
  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      if (typeof $ !== 'undefined') {
        $(modalId).modal('show');
      }
      clearTable();
      if (fileInput) fileInput.value = '';
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', e => {
      fileObj = e.target.files[0] || null;
      if (!fileObj) {
        clearTable();
        return;
      }
      currentPage = 1;
      fetchPreview(currentPage);
    });
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage -= 1;
        fetchPreview(currentPage);
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      currentPage += 1;
      fetchPreview(currentPage);
    });
  }

  if (btnProcesar) {
    btnProcesar.addEventListener('click', () => processFile(false));
  }

  // ---------- Reproceso por CÓDIGO de centro (Opción A con pop-up) ----------
  function showReprocessMessage(kind, text) {
    if (!outReprocess) return;
    outReprocess.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-info');
    outReprocess.classList.add(kind);
    outReprocess.textContent = text;
  }

  if (btnReprocesar && modalReprocesarEl && inputCodigo && btnConfirmReprocesar && reprocessUrl) {
    // Abre el modal para ingresar CÓDIGO
    btnReprocesar.addEventListener('click', () => {
      if (modalReprocesar) modalReprocesar.show();
      else modalReprocesarEl.style.display = 'block';

      inputCodigo.value = '';
      setTimeout(() => inputCodigo.focus(), 150);
    });

    // Confirma y envía POST con CÓDIGO
    btnConfirmReprocesar.addEventListener('click', async () => {
      const codigo = (inputCodigo.value || '').trim();
      if (!codigo) {
        showReprocessMessage('alert-danger', 'Debés ingresar un código de centro.');
        inputCodigo.focus();
        return;
      }

      btnConfirmReprocesar.disabled = true;
      showReprocessMessage('alert-info', `Procesando centro ${codigo}...`);

      try {
        const resp = await fetch(reprocessUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': window.csrfToken || getCookie(CSRF_COOKIE_NAME),
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({ codigo }).toString(),
        });

        const data = await resp.json();
        if (!resp.ok || !data.ok) {
          const msg = (data && (data.error || data.detail)) || `HTTP ${resp.status}`;
          showReprocessMessage('alert-danger', `Error: ${msg}`);
        } else {
          const proc = data.procesados ?? 0;
          const imp = data.impactados ?? 0;
          showReprocessMessage('alert-success', `OK. Procesados: ${proc} | Impactados: ${imp}`);
          if (modalReprocesar) modalReprocesar.hide();
          else modalReprocesarEl.style.display = 'none';
        }
      } catch (e) {
        showReprocessMessage('alert-danger', `Error de red: ${e.message}`);
      } finally {
        btnConfirmReprocesar.disabled = false;
      }
    });
  }
})();
