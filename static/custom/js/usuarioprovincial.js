document.addEventListener('DOMContentLoaded', function () {
  const chk = document.getElementById('id_es_usuario_provincial');
  const sel = document.getElementById('id_provincia');
  if (!chk || !sel) return;

  function getWrapper(el) {
    // intenta encontrar el contenedor del campo (crispy/bootstrap)
    return el.closest('.form-group, .mb-3, .form-row, .form-group.row') || el.parentElement;
  }

  const wrapper = getWrapper(sel);
  const select2Container = document.querySelector('#id_provincia ~ .select2'); // contenedor select2 si existe

  function showProvincia(show) {
    const display = show ? '' : 'none';
    if (wrapper) wrapper.style.display = display;
    // si usás select2, también esconder su contenedor
    if (select2Container) select2Container.style.display = display;

    if (!show) {
      sel.value = '';
      // sincroniza si hay select2 cargado
      if (typeof $ !== 'undefined' && $.fn && $.fn.select2) {
        $('#id_provincia').val(null).trigger('change');
      }
    }
  }

  // estado inicial e interacción
  showProvincia(chk.checked);
  chk.addEventListener('change', function () {
    showProvincia(chk.checked);
  });
});

