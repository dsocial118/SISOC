// static/custom/js/celiaquia.js
(function(){
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
  }

  function validarCelda(celda) {
    const columna = celda.dataset.columna;
    const valor = celda.textContent.trim();
    let error = null;
    
    // Validaciones según columna
    if (columna === 'documento') {
      if (!valor) {
        error = 'Campo obligatorio vacío';
      } else if (!/^\d+$/.test(valor)) {
        error = 'Debe contener solo dígitos';
      }
    } else if (columna === 'email' && valor) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
        error = 'Formato de email inválido';
      }
    } else if (columna === 'fecha_nacimiento') {
      if (!valor) {
        error = 'Campo obligatorio vacío';
      }
    } else if (['apellido', 'nombre'].includes(columna)) {
      if (!valor) {
        error = 'Campo obligatorio vacío';
      }
    } else if (['telefono', 'altura', 'codigo_postal'].includes(columna) && valor) {
      if (!/^\d+$/.test(valor)) {
        error = 'Debe contener solo dígitos';
      }
    }
    
    // Aplicar estilo según validación
    if (error) {
      celda.classList.add('table-danger');
      celda.title = error;
    } else {
      celda.classList.remove('table-danger');
      celda.title = '';
    }
    
    // Actualizar estado del botón submit
    actualizarEstadoBotonSubmit();
  }
  
  function actualizarEstadoBotonSubmit() {
    const btnSubmit = document.getElementById('btn-submit');
    if (!btnSubmit) return;
    
    const celdasConError = document.querySelectorAll('.editable-cell.table-danger');
    if (celdasConError.length > 0) {
      btnSubmit.disabled = true;
      btnSubmit.title = 'Corrija los errores antes de crear el expediente';
    } else {
      btnSubmit.disabled = false;
      btnSubmit.title = '';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const btnPreview = document.getElementById('btn-preview');
    const btnSubmit = document.getElementById('btn-submit');
    const errorEl = document.getElementById('preview-error');
    const headerRow = document.getElementById('preview-headers');
    const bodyRows = document.getElementById('preview-rows');
    const container = document.getElementById('preview-container');
    const validationErrors = document.getElementById('validation-errors');
    const errorsList = document.getElementById('errors-list');

    if (!btnPreview) return;
    if (errorEl) errorEl.textContent = '';

    btnPreview.addEventListener('click', async () => {
      if (errorEl) errorEl.textContent = '';
      headerRow.innerHTML = '';
      bodyRows.innerHTML = '';
      if (validationErrors) validationErrors.classList.add('d-none');
      if (errorsList) errorsList.innerHTML = '';

      if (!window.PREVIEW_URL) {
        if (errorEl) errorEl.textContent = 'URL de previsualización no configurada.';
        return;
      }

      const fileInput = document.querySelector('input[name="excel_masivo"]');
      if (!fileInput || !fileInput.files.length) {
        if (errorEl) errorEl.textContent = 'Primero seleccioná un archivo Excel.';
        return;
      }

      btnPreview.disabled = true;
      const originalText = btnPreview.innerHTML;
      btnPreview.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Cargando...';

      const formData = new FormData();
      formData.append('excel_masivo', fileInput.files[0]);
      formData.append('limit', 'all');
      
      // Guardar referencia al archivo para regenerarlo después
      window.currentExcelFile = fileInput.files[0];

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

        // Mostrar errores de validación
        if (data.errores && data.errores.length > 0) {
          const erroresHTML = data.errores.map(err => 
            `<div class="mb-1"><strong>⚠️ Registro ${err.fila}, columna "${err.columna}":</strong> ${err.mensaje}</div>`
          ).join('');
          if (errorsList) errorsList.innerHTML = erroresHTML;
          if (validationErrors) validationErrors.classList.remove('d-none');
          
          // Deshabilitar botón de guardar si hay errores
          if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.title = 'Corrija los errores antes de crear el expediente';
          }
        } else {
          // Habilitar botón de guardar si no hay errores
          if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.title = '';
          }
        }

        // Renderizar tabla de preview con celdas editables
        const headers = data.headers;
        const rows = data.rows;
        const erroresPorCelda = {};
        
        // Indexar errores por fila y columna
        if (data.errores) {
          data.errores.forEach(err => {
            const key = `${err.fila}-${err.columna}`;
            erroresPorCelda[key] = err.mensaje;
          });
        }
        
        headerRow.innerHTML = headers.map(h => `<th>${h}</th>`).join('');
        bodyRows.innerHTML = rows.map((row, idx) => {
          const fila = idx + 1;
          const cells = headers.map(h => {
            const valor = row[h] || '';
            const key = `${fila}-${h}`;
            const tieneError = erroresPorCelda[key];
            const claseError = tieneError ? 'table-danger' : '';
            const titulo = tieneError ? `title="${erroresPorCelda[key]}"` : '';
            
            // Solo hacer editables las columnas que no son ID
            if (h === 'ID') {
              return `<td class="${claseError} text-center fw-bold">${valor}</td>`;
            }
            return `<td class="${claseError} editable-cell" contenteditable="true" data-fila="${fila}" data-columna="${h}" ${titulo}>${valor}</td>`;
          }).join('');
          return `<tr>${cells}</tr>`;
        }).join('');
        
        // Actualizar contador
        const previewCount = document.getElementById('preview-count');
        if (previewCount) {
          previewCount.textContent = `${rows.length} registros`;
        }
        
        // Agregar listeners para validar al editar
        document.querySelectorAll('.editable-cell').forEach(cell => {
          cell.addEventListener('blur', function() {
            validarCelda(this);
          });
          cell.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
              e.preventDefault();
              this.blur();
            }
          });
        });
        
        container.classList.remove('d-none');

      } catch (err) {
        console.error(err);
        if (errorEl) errorEl.textContent = 'Error al previsualizar: ' + err.message;
      } finally {
        btnPreview.disabled = false;
        btnPreview.innerHTML = originalText;
      }
    });
    
    // Interceptar el submit del formulario para incluir datos editados
    const form = document.getElementById('expediente-form');
    if (form) {
      form.addEventListener('submit', function(e) {
        const celdas = document.querySelectorAll('.editable-cell');
        if (celdas.length === 0) return; // No hay preview, continuar normal
        
        e.preventDefault();
        
        // Recopilar datos editados
        const datosEditados = [];
        const filas = {};
        
        celdas.forEach(celda => {
          const fila = celda.dataset.fila;
          const columna = celda.dataset.columna;
          const valor = celda.textContent.trim();
          
          if (!filas[fila]) filas[fila] = {};
          filas[fila][columna] = valor;
        });
        
        // Convertir a array
        Object.keys(filas).forEach(fila => {
          datosEditados.push(filas[fila]);
        });
        
        // Agregar datos editados como campo oculto JSON
        const inputDatos = document.createElement('input');
        inputDatos.type = 'hidden';
        inputDatos.name = 'datos_editados';
        inputDatos.value = JSON.stringify(datosEditados);
        form.appendChild(inputDatos);
        
        // Enviar formulario
        form.submit();
      });
    }
  });
})();
