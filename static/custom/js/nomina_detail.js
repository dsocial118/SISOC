document.addEventListener("DOMContentLoaded", function() {
  // Función para toggle de estadísticas detalladas
  function toggleDetailedStats() {
    const content = document.getElementById('detailedStatsContent');
    const icon = document.querySelector('.nomina-toggle-icon');
    const button = document.querySelector('.nomina-toggle-details span');

    if (!content || !icon || !button) {
      console.error('No se encontraron elementos para el toggle de estadísticas');
      return;
    }

    if (content.style.display === 'none' || content.style.display === '') {
      content.style.display = 'block';
      icon.classList.add('rotated');
      button.textContent = 'Ocultar estadísticas detalladas';
      localStorage.setItem('nominaDetailsExpanded', 'true');
    } else {
      content.style.display = 'none';
      icon.classList.remove('rotated');
      button.textContent = 'Ver estadísticas detalladas';
      localStorage.setItem('nominaDetailsExpanded', 'false');
    }
  }

  // Agregar event listener al botón de toggle
  const toggleButton = document.querySelector('.nomina-toggle-details');
  if (toggleButton) {
    toggleButton.addEventListener('click', toggleDetailedStats);
  }

  // Restaurar estado al cargar la página
  if (localStorage.getItem('nominaDetailsExpanded') === 'true') {
    toggleDetailedStats();
  }

  const modalEl = document.getElementById("editarNominaModal");
  const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
  const modalBody = document.querySelector("#editarNominaModal .modal-body");
  const modalForm = document.getElementById("editarNominaForm");

  function renderModalError(message) {
    if (!modalBody) {
      return;
    }
    modalBody.innerHTML = "";
    const div = document.createElement("div");
    div.classList.add("alert", "alert-danger", "mb-0");
    div.textContent = message || "Ocurrió un error al cargar el formulario.";
    modalBody.appendChild(div);
  }

  document.querySelectorAll(".editar-nomina").forEach(function(btn) {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      const id = this.dataset.id;
      const editUrl = this.dataset.editUrl || `/comedores/editar-nomina/${id}/`;

      fetch(editUrl)
        .then(function(response) {
          if (!response.ok) {
            throw new Error("No se pudo cargar el formulario de edición.");
          }
          return response.text();
        })
        .then(html => {
          if (!modalBody || !modalForm || !modal) {
            return;
          }
          modalBody.innerHTML = html;
          modalForm.action = editUrl;
          modal.show();
        })
        .catch(function(error) {
          if (modalBody && modal) {
            renderModalError(error.message);
            modal.show();
          }
        });
    });
  });

  if (!modalForm) {
    return;
  }

  modalForm.addEventListener("submit", function(e) {
    e.preventDefault();

    if (!modalForm.action) {
      renderModalError("No se encontró la URL de edición.");
      return;
    }

    const formData = new FormData(modalForm);
    fetch(modalForm.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": formData.get('csrfmiddlewaretoken')
      },
      body: formData
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error("No se pudieron guardar los cambios.");
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        if (modal) {
          modal.hide();
        }
        location.reload();
      } else {
        if (!modalBody) {
          return;
        }
        modalBody.innerHTML = "";
        for (const field in data.errors) {
          const div = document.createElement("div");
          div.classList.add("text-danger");
          div.textContent = `${field}: ${data.errors[field].join(", ")}`;
          modalBody.appendChild(div);
        }
      }
    })
    .catch(function(error) {
      renderModalError(error.message || "Ocurrió un error al guardar.");
    });
  });
});
