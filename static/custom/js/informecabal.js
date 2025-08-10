// static/custom/js/informecabal.js
// [Informe Cabal - JS]
// - Maneja modal, preview AJAX paginado (25), spinner y proceso final.
// - Mensajes Bootstrap fade show.

(function () {
  const btnOpen = document.getElementById('btn-open-modal');
  const modalId = '#modalCabal';
  const fileInput = document.getElementById('fileCabal');
  const tableBody = document.querySelector('#preview-table tbody');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const pageIndicator = document.getElementById('page-indicator');
  const btnProcesar = document.getElementById('btn-procesar');
  const alertZone = document.getElementById('alert-zone');

  let currentPage = 1;
  let totalRows = 0;
  let fileObj = null;

  function showAlert(msg, type = 'warning') {
    if (!alertZone) return;
    const div = document.createElement('div');
    div.className = `alert alert-${type} fade show`;
    div.role = 'alert';
    div.innerHTML = msg;
    alertZone.innerHTML = '';
    alertZone.appendChild(div);
  }

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
      const d = r.data;
      const tr = document.createElement('tr');
      if (r.no_coincidente) tr.classList.add('table-warning');
      tr.innerHTML = `
        <td>${r.fila}</td>
        <td>${d.NroComercio}</td>
        <td>${d.RazonSocial || ''}</td>
        <td>${d.Importe || ''}</td>
        <td>${d.FechaTRX || ''}</td>
        <td>${d.MonedaOrigen || ''}</td>
        <td>${d.ImportePesos || ''}</td>
        <td>${d.MotivoRechazo || ''}</td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function updatePager() {
    const totalPages = Math.ceil(totalRows / 25);
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
      headers: { 'X-CSRFToken': window.csrfToken },
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
      headers: { 'X-CSRFToken': window.csrfToken },
      body: form
    })
      .then(r => r.json().then(j => ({ status: r.status, body: j })))
      .then(({ status, body }) => {
        if (spinner) spinner.classList.add('d-none');
        if (body.ok) {
          showAlert(`Archivo procesado. Total: ${body.total}, Válidas: ${body.validas}, Inválidas: ${body.invalidas}`, 'success');
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

  // Eventos
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

  // ——— (Opcional) Código de reproceso por centro: si no usás estos IDs, no pasa nada ———
  const btnReprocesarCentro = document.getElementById('btn-reprocesar-centro');
  const modalReprocesar = typeof $ !== 'undefined' ? $('#modalReprocesarCentro') : null;
  const btnConfirmReprocesar = document.getElementById('btnConfirmReprocesar');

  if (btnReprocesarCentro && modalReprocesar) {
    btnReprocesarCentro.addEventListener('click', () => {
      modalReprocesar.modal('show');
    });
  }

  if (btnConfirmReprocesar) {
    btnConfirmReprocesar.addEventListener('click', () => {
      const codigoEl = document.getElementById('codigoCentro');
      const codigo = (codigoEl ? codigoEl.value : '').trim();
      if (!codigo) {
        alert('Debe ingresar un código de comedor.');
        return;
      }
      if (!confirm(`¿Seguro que deseas reprocesar el centro ${codigo}?`)) return;

      fetch(window.urls.informecabal_reprocess, {
        method: 'POST',
        headers: {
          'X-CSRFToken': window.csrfToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ centro: codigo })
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            alert(`Centro ${codigo} reprocesado correctamente.`);
            if (modalReprocesar) modalReprocesar.modal('hide');
            location.reload();
          } else {
            alert(data.error || 'Ocurrió un error al reprocesar.');
          }
        })
        .catch(err => {
          console.error(err);
          alert('Error de conexión al reprocesar.');
        });
    });
  }
})();
