document.addEventListener('DOMContentLoaded', function () {
    const tipoField = document.getElementById('id_tipo');
    const allFieldWrappers = document.querySelectorAll('div[id^="div_id_"]');

    const camposComunes = ['div_id_tipo'];
    const camposFaro = [
        'div_id_nombre',
        'div_id_codigo',
        'div_id_direccion',
        'div_id_contacto',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo'
    ];
    const camposAdherido = [
        'div_id_nombre',
        'div_id_codigo',
        'div_id_direccion',
        'div_id_contacto',
        'div_id_faro_asociado',
        'div_id_tipo_organizacion',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo'
    ];

    function toggleCampos() {
        const visibleFields = tipoField.value === 'faro'
            ? camposComunes.concat(camposFaro)
            : tipoField.value === 'adherido'
            ? camposComunes.concat(camposAdherido)
            : camposComunes;

        allFieldWrappers.forEach(div => {
            div.style.display = visibleFields.includes(div.id) ? 'block' : 'none';
        });
    }

    if (tipoField) {
        tipoField.addEventListener('change', toggleCampos);
        toggleCampos();
    }
});
