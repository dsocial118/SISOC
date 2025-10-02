// static/custom/js/celiaquia.js
(function(){
  // PREVIEW_URL debe definirse en la plantilla antes de este script:
  // <script>const PREVIEW_URL = "{% url 'expediente_preview_excel' %}";</script>

  /**
   * Obtiene el valor de una cookie por nombre.
   */
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const btnPreview = document.getElementById('btn-preview');
    const errorEl    = document.getElementById('preview-error');
    const headerRow  = document.getElementById('preview-headers');
    const bodyRows   = document.getElementById('preview-rows');
    const container  = document.getElementById('preview-container');

    if (!btnPreview) return;
    if (errorEl) errorEl.textContent = '';

    btnPreview.addEventListener('click', async () => {
      // Limpiar estado
      if (errorEl) errorEl.textContent = '';
      headerRow.innerHTML = '';
      bodyRows.innerHTML  = '';

      // Validar URL
      if (!window.PREVIEW_URL) {
        if (errorEl) errorEl.textContent = 'URL de previsualización no configurada.';
        return;
      }

      // Validar selección de archivo
      const fileInput = document.querySelector('input[name="excel_masivo"]');
      if (!fileInput || !fileInput.files.length) {
        if (errorEl) errorEl.textContent = 'Primero seleccioná un archivo Excel.';
        return;
      }

      // Deshabilitar botón y mostrar spinner
      btnPreview.disabled = true;
      const originalText = btnPreview.innerHTML;
      btnPreview.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Cargando...';

      const formData = new FormData();
      formData.append('excel_masivo', fileInput.files[0]);
      formData.append('limit', 'all');

      try {
        const response = await fetch(window.PREVIEW_URL, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
          },
          body: formData
        });

        if (!response.ok) {
          let msg = `HTTP ${response.status}`;
          try {
            const errJson = await response.json();
            msg = errJson.error || msg;
          } catch {}
          throw new Error(msg);
        }

        const contentType = response.headers.get('Content-Type') || '';
        if (!contentType.includes('application/json')) {
          const text = await response.text();
          console.error('Respuesta inesperada:', text);
          throw new Error('Respuesta inesperada del servidor');
        }

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        // Renderizar tabla de preview con dicts
        const headers = data.headers;
        const rows    = data.rows;
        headerRow.innerHTML = headers.map(h => `<th>${h}</th>`).join('');
        bodyRows.innerHTML  = rows.map(row => {
          const cells = headers.map(h => `<td>${row[h] || ''}</td>`).join('');
          return `<tr>${cells}</tr>`;
        }).join('');
        container.classList.remove('d-none');

      } catch (err) {
        console.error(err);
        if (errorEl) errorEl.textContent = 'Error al previsualizar: ' + err.message;
      } finally {
        btnPreview.disabled = false;
        btnPreview.innerHTML = originalText;
      }
    });
  });
})();
