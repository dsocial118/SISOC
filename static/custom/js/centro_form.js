document.addEventListener('DOMContentLoaded', function () {
    const tipoField = document.getElementById('id_tipo');
    const allFieldWrappers = document.querySelectorAll('div[id^="div_id_"]');

        document.getElementById('id_provincia').addEventListener('change', function () {
        var url = ajaxLoadMunicipiosUrl;  // Obtén la URL de la vista
        var provinciaId = this.value;  // Obtén el ID de la provincia seleccionada
        fetch(url + '?provincia_id=' + provinciaId)
            .then(response => response.json())
            .then(data => {
                var municipioSelect = document.getElementById('id_municipio');
                municipioSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (municipio) {
                    var option = document.createElement('option');
                    option.value = municipio.id;
                    option.setAttribute('data-municipio-id', municipio.id);  // Añadir propiedad personalizada
                    option.textContent = municipio.nombre;
                    municipioSelect.appendChild(option);
                });
            });
    });

    
    document.getElementById('id_municipio').addEventListener('change', function () {
        var url = ajaxLoadLocalidadesUrl;  // Obtén la URL de la vista
        var localidadId = this.options[this.selectedIndex].getAttribute('data-municipio-id');;  // Obtén el ID de la provincia seleccionada
        fetch(url + '?municipio_id=' + localidadId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_localidad');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (localidad) {
                    var option = document.createElement('option');
                    option.value = localidad.id;
                    option.textContent = localidad.nombre;
                    localidadSelect.appendChild(option);
                });
            });
    });
    const camposComunes = ['div_id_tipo'];
    const camposFaro = [
        'div_id_nombre',
        'div_id_codigo',
        'div_id_organizacion_asociada',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo',
        'div_id_provincia',  
        'div_id_municipio',  
        'div_id_localidad',  
        'div_id_calle',  
        'div_id_numero',  
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
        'div_id_organizacion_asociada',
        'div_id_faro_asociado',
        'div_id_foto',
        'div_id_referente',
        'div_id_activo',
        'div_id_provincia',  
        'div_id_municipio',  
        'div_id_localidad',  
        'div_id_calle',  
        'div_id_numero',  
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


