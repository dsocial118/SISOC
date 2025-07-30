document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-process-expediente');
  if (btn) {
    console.log('Process URL:', PROCESS_URL);

    const msgContainer = document.createElement('div');
    msgContainer.id = 'process-msg';
    const previewCard = document.querySelector('.card.mb-4');
    if (previewCard) previewCard.parentNode.insertBefore(msgContainer, previewCard);

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      const origHTML = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...';

      try {
        const resp = await fetch(PROCESS_URL, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1],
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
            El expediente ha pasado al estado <strong>EN ESPERA</strong>.
            ${data.errores ? `<br><small class="text-danger">${data.errores} errores.</small>` : ''}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        `;
        setTimeout(() => window.location.reload(), 2000);

      } catch (err) {
        console.error('Error procesar expediente:', err);
        msgContainer.innerHTML = `
          <div class="alert alert-danger" role="alert">
            Error al procesar expediente: ${err.message}
          </div>
        `;
        btn.disabled = false;
        btn.innerHTML = origHTML;
      }
    });
  }
  //Actualizar archivo modal
  const modal = document.getElementById('modalSubirArchivo');
  modal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const legajoId = button.getAttribute('data-legajo-id');
    const expedienteId = button.getAttribute('data-expediente-id');

    const form = modal.querySelector('#form-subir-archivo');
    form.action = `/expedientes/${expedienteId}/legajo/${legajoId}/archivo/`;
  });

  // Modal de subida de archivo
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

      // Limpiar mensajes anteriores
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
            'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1]
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
        }, 1500);

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
});
