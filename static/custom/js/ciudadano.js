document.addEventListener('DOMContentLoaded', () => {
  $('.select2').select2({ theme: 'bootstrap5' });

  $('#agregar-programa-btn').click(() => $('#form-programas').toggleClass('d-none'));
  $('#cancelar-btn').click(() => $('#form-programas').toggleClass('d-none'));

  $('#ProgramaForm').on('submit', function(e) {
    e.preventDefault();
    $.post(this.action, $(this).serialize(), data => {
      data.programas.forEach(pr => {
        const html = `
          <div class="col-md-6 ease-out">
            <div class="card shadow-sm">
              <div class="card-body d-flex justify-content-between">
                <span class="text-truncate">${pr.nombre}</span>
                <button class="btn btn-sm btn-outline-danger borrar-programa" data-program-id="${pr.id}">×</button>
              </div>
            </div>
          </div>`;
        $('#progamas_ciudadanos .row').append(html);
      });
      $('#form-programas').addClass('d-none');
    });
  });

  $(document).on('click', '.borrar-programa', function() {
    const btn = $(this), id = btn.data('program-id');
    if (!confirm('¿Eliminar programa?')) return;
    $.post('{% url "eliminar_programa" %}', { csrfmiddlewaretoken: '{{ csrf_token }}', program_id: id }, resp => {
      if (resp.success) btn.closest('.col-md-6').remove();
    });
  });
});

