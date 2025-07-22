document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-process-expediente');
  if (!btn) return;

  console.log('Process URL:', PROCESS_URL);

  // Contenedor para mensajes de proceso
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

      console.log('Process status:', resp.status);
      console.log('Content-Type:', resp.headers.get('Content-Type'));
      const raw = await resp.text();
      console.log('Raw response:', raw);

      if (resp.status !== 200) {
        throw new Error(`HTTP ${resp.status}: ${raw.trim()}`);
      }

      let data;
      try {
        data = JSON.parse(raw);
      } catch (e) {
        throw new Error(`Invalid JSON response: ${raw.trim()}`);
      }

      if (!data.success) {
        throw new Error(data.error || 'Server returned success=false');
      }

      msgContainer.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
          <strong>¡Listo!</strong> Se crearon ${data.creados} legajos.
          ${data.errores ? `<br><small class="text-danger">${data.errores} errores.</small>` : ''}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;
      // Recarga para actualizar tabla
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
});
