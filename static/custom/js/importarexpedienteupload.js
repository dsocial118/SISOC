document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('csv-upload-form');
    const btn = document.getElementById('csv-upload-btn');
    if (!form || !btn) return;
    form.addEventListener('submit', function () {
        // Evitar múltiples envíos mientras se procesa
        btn.disabled = true;
        btn.classList.add('disabled');
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando…';
    });
});
