document.addEventListener('DOMContentLoaded', function () {
    const tipoField = document.getElementById('id_tipo');
    const faroFieldWrapper = document.getElementById('div_id_faro_asociado');

    if (tipoField && faroFieldWrapper) {
        function toggleFaroField() {
            if (tipoField.value === 'adherido') {
                faroFieldWrapper.style.display = 'block';
            } else {
                faroFieldWrapper.style.display = 'none';
                const faroInput = document.getElementById('id_faro_asociado');
                if (faroInput) faroInput.value = '';
            }
        }

        tipoField.addEventListener('change', toggleFaroField);
        toggleFaroField();
    }
});
