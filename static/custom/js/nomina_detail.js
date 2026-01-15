document.addEventListener("DOMContentLoaded", function() {
  const modal = new bootstrap.Modal(document.getElementById('editarNominaModal'));
  const modalBody = document.querySelector("#editarNominaModal .modal-body");
  const modalForm = document.getElementById("editarNominaForm");

  // Funcionalidad de búsqueda
  const searchInput = document.getElementById("nominaSearch");
  if (searchInput) {
    searchInput.addEventListener("input", function() {
      const searchTerm = this.value.toLowerCase();
      const tableRows = document.querySelectorAll(".nomina-table-row");

      tableRows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }

  document.querySelectorAll(".editar-nomina").forEach(function(btn) {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      const id = this.dataset.id;

      fetch(`/comedores/editar-nomina/${id}/`)
        .then(response => response.text())
        .then(html => {
          modalBody.innerHTML = html;
          modalForm.action = `/comedores/editar-nomina/${id}/`;
          modal.show();
        });
    });
  });

  modalForm.addEventListener("submit", function(e) {
    e.preventDefault();

    const formData = new FormData(modalForm);
    fetch(modalForm.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": formData.get('csrfmiddlewaretoken')
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        modal.hide();
        location.reload();
      } else {
        modalBody.innerHTML = "";
        for (const field in data.errors) {
          const div = document.createElement("div");
          div.classList.add("text-danger");
          div.textContent = `${field}: ${data.errors[field].join(", ")}`;
          modalBody.appendChild(div);
        }
      }
    });
  });
});
