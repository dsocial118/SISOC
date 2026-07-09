(function () {
    var derivarUrl = null;
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    var csrfToken = csrfInput ? csrfInput.value : '';

    function $(id) { return document.getElementById(id); }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.nomina-derivar-btn');
        if (!btn) return;
        derivarUrl = btn.dataset.url;
        $('derivarNombreCiudadano').textContent = btn.dataset.ciudadano || '';
        $('derivarCentroSelect').value = '';
        $('derivarMotivo').value = '';
        var msg = $('derivarMensaje');
        msg.classList.add('d-none');
        msg.textContent = '';
    });

    var confirmarBtn = $('derivarConfirmarBtn');
    if (!confirmarBtn) return;

    confirmarBtn.addEventListener('click', function () {
        var centroId = $('derivarCentroSelect').value;
        var motivo = $('derivarMotivo').value;
        var msg = $('derivarMensaje');

        if (!centroId) {
            msg.className = 'alert alert-warning';
            msg.textContent = 'Seleccioná un centro destino.';
            return;
        }

        confirmarBtn.disabled = true;

        fetch(derivarUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'centro_destino_id=' + encodeURIComponent(centroId) +
                  '&motivo=' + encodeURIComponent(motivo),
        })
        .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
            if (res.data && res.data.success) {
                var modalEl = $('derivarNominaModal');
                if (modalEl && window.bootstrap) {
                    var instance = bootstrap.Modal.getInstance(modalEl);
                    if (instance) instance.hide();
                }
                window.location.reload();
            } else {
                msg.className = 'alert alert-danger';
                msg.textContent = (res.data && res.data.message) || 'Error al derivar.';
                confirmarBtn.disabled = false;
            }
        })
        .catch(function () {
            msg.className = 'alert alert-danger';
            msg.textContent = 'Error de conexión. Intentá nuevamente.';
            confirmarBtn.disabled = false;
        });
    });
})();
