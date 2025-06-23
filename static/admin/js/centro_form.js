document.addEventListener('DOMContentLoaded', function () {
    const tipoField = document.getElementById('id_tipo');
    const allFieldWrappers = document.querySelectorAll('div[id^="div_id_"]');

    const camposComunes = ['div_id_tipo'];
    const camposFaro = [
        'div_id_nombre',
        'div_id_codigo',
        'div_id_organizacionasociada',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo',
        'div_id_domicilio_sede',  // ← agregado
        'div_id_domicilio_actividad',
        'div_id_telefono',
        'div_id_celular',
        'div_id_correo',
        'div_id_sitioweb',
        'div_id_linkredes',
        'div_id_nombre_referente',
        'div_id_apellido_referente',
        'div_id_telefono_referente',
        'div_id_correo_referente'
    ];

    const camposAdherido = [
        'div_id_nombre',
        'div_id_codigo',
        'div_id_organizacionasociada',
        'div_id_faro_asociado',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo',
        'div_id_domicilio_sede',  // ← agregado
        'div_id_domicilio_actividad',
        'div_id_telefono',
        'div_id_celular',
        'div_id_correo',
        'div_id_sitioweb',
        'div_id_linkredes',
        'div_id_nombre_referente',
        'div_id_apellido_referente',
        'div_id_telefono_referente',
        'div_id_correo_referente'   

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
