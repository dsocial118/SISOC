

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('id_nacionalidad').classList.add('select2');

    document.getElementById('id_fk_provincia').addEventListener('change', function() {
        var url = ajaxLoadMunicipiosUrl;  // Obtén la URL de la vista
        var provinciaId = this.value;  // Obtén el ID de la provincia seleccionada

        fetch(url + '?provincia_id=' + provinciaId)
            .then(response => response.json())
            .then(data => {
                var municipioSelect = document.getElementById('id_fk_municipio');
                municipioSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function(municipio) {
                    var option = document.createElement('option');
                    option.value = municipio.id;
                    option.setAttribute('data-departamento-id', municipio.departamento_id);  // Añadir propiedad personalizada
                    option.textContent = municipio.nombre_region;
                    municipioSelect.appendChild(option);
                });
            });
    });

    document.getElementById('id_fk_municipio').addEventListener('change', function() {
        var url = ajaxLoadLocalidadesUrl;  // Obtén la URL de la vista
        var localidadId = this.options[this.selectedIndex].getAttribute('data-departamento-id');;  // Obtén el ID de la provincia seleccionada

        fetch(url + '?municipio_id=' + localidadId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_fk_localidad');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function(localidad) {
                    var option = document.createElement('option');
                    option.value = localidad.id;
                    option.textContent = localidad.nombre;
                    localidadSelect.appendChild(option);
                });
            });
    });

  
});


$(document).ready(function() {
    $('#id_nacionalidad').select2();
});

id_foto.onchange = (evt) => {
    const [file] = id_foto.files;
    if (file) {
        blah.src = URL.createObjectURL(file);
    }
};