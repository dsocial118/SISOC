// static/js/informecabal.js
// [Informe Cabal - JS]
// - Maneja modal, preview AJAX paginado (25), spinner y proceso final.
// - Mensajes Bootstrap fade show.

(function() {
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

  function showAlert(msg, type='warning') {
    const div = document.createElement('div');
    div.className = `alert alert-${type} fade show`;
    div.role = 'alert';
    div.innerHTML = msg;
    alertZone.innerHTML = '';
    alertZone.appendChild(div);
  }

  function clearTable() {
    tableBody.innerHTML = `<tr><td colspan="8" class="text-center">Sin datos</td></tr>`;
    totalRows = 0;
    currentPage = 1;
    pageIndicator.textContent = '1';
    btnPrev.disabled = true;
    btnNext.disabled = true;
    btnProcesar.disabled = true;
  }

  function renderRows(rows) {
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
    pageIndicator.textContent = String(currentPage);
    btnPrev.disabled = currentPage <= 1;
    btnNext.disabled = currentPage >= totalPages || totalPages <= 1;
  }

  function fetchPreview(page=1) {
    if (!fileObj) return;
    const form = new FormData();
    form.append('file', fileObj);
    form.append('page', String(page));

    btnProcesar.disabled = true;
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
      btnProcesar.disabled = false;
      updatePager();

      if (j.not_matching && j.not_matching.length) {
        showAlert(`Registros no coincidentes: (${j.not_matching.join(', ')})`, 'warning');
      } else {
        alertZone.innerHTML = '';
      }
    })
    .catch(() => {
      showAlert('Error inesperado al previsualizar', 'danger');
      clearTable();
    });
  }

  function processFile(force=false) {
    if (!fileObj) return;
    const form = new FormData();
    form.append('file', fileObj);
    form.append('force', force ? 'true' : 'false');

    const spinner = document.getElementById('spin-procesar');
    spinner.classList.remove('d-none');
    btnProcesar.disabled = true;

    fetch(window.urls.informecabal_process, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.csrfToken },
      body: form
    })
    .then(r => r.json().then(j => ({ status: r.status, body: j })))
    .then(({ status, body }) => {
      spinner.classList.add('d-none');
      if (body.ok) {
        showAlert(`Archivo procesado. Total: ${body.total}, Válidas: ${body.validas}, Inválidas: ${body.invalidas}`, 'success');
        btnProcesar.disabled = true;
        // Recargar página para ver historial actualizado
        setTimeout(() => window.location.reload(), 800);
        return;
      }
      if (status === 409 && body.duplicate_name) {
        // Confirmación por nombre duplicado
        if (confirm('Ya se subió un archivo con este nombre. ¿Desea proseguir?')) {
          processFile(true);
        } else {
          btnProcesar.disabled = false;
        }
        return;
      }
      showAlert(body.error || 'Error al procesar', 'danger');
      btnProcesar.disabled = false;
    })
    .catch(() => {
      spinner.classList.add('d-none');
      showAlert('Error inesperado al procesar', 'danger');
      btnProcesar.disabled = false;
    });
  }

  // Eventos
  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      $(modalId).modal('show');
      clearTable();
      fileInput.value = '';
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

  btnPrev.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage -= 1;
      fetchPreview(currentPage);
    }
  });
  btnNext.addEventListener('click', () => {
    currentPage += 1;
    fetchPreview(currentPage);
  });
  btnProcesar.addEventListener('click', () => processFile(false));



  const btnReprocesarCentro = document.getElementById('btn-reprocesar-centro');
  const modalReprocesar = $('#modalReprocesarCentro');
  const btnConfirmReprocesar = document.getElementById('btnConfirmReprocesar');

  if (btnReprocesarCentro) {
    btnReprocesarCentro.addEventListener('click', () => {
      modalReprocesar.modal('show');
    });
  }

  if (btnConfirmReprocesar) {
    btnConfirmReprocesar.addEventListener('click', () => {
      const codigo = document.getElementById('codigoCentro').value.trim();
      if (!codigo) {
        alert("Debe ingresar un código de comedor.");
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
          modalReprocesar.modal('hide');
          location.reload();
        } else {
          alert(data.error || "Ocurrió un error al reprocesar.");
        }
      })
      .catch(err => {
        console.error(err);
        alert("Error de conexión al reprocesar.");
      });
    });
  }

});
