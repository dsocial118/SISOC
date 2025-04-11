

document.addEventListener('DOMContentLoaded', function () {

    document.getElementById('id_provincia').addEventListener('change', function () {
        var url = ajaxLoadMunicipiosUrl;  // Obtén la URL de la vista
        var provinciaId = this.value;  // Obtén el ID de la provincia seleccionada
        var url2 = ajaxLoadDepartamentosUrl;  // Obtén la URL de la vista
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

        fetch(url2 + '?provincia_id=' + provinciaId)
            .then(response => response.json())
            .then(data => {
                var departamentoSelect = document.getElementById('id_fk_departamento');
                departamentoSelect.innerHTML = '';  // Limpia el campo de departamentos

                data.forEach(function (departamento) {
                    var option = document.createElement('option');
                    option.value = departamento.id;
                    option.setAttribute('data-departamento-id', departamento.id);  // Añadir propiedad personalizada
                    option.textContent = departamento.nombre;
                    departamentoSelect.appendChild(option);
                });
            });
    });

    document.getElementById('id_municipio').addEventListener('change', function () {
        var url = ajaxLoadLocalidadesUrl;  // Obtén la URL de la vista
        var localidadId = this.options[this.selectedIndex].getAttribute('data-municipio-id');;  // Obtén el ID de la provincia seleccionada
        var url2 = ajaxLoadAsentameintosUrl;
        fetch(url + '?municipio_id=' + localidadId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_fk_localidad');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (localidad) {
                    var option = document.createElement('option');
                    option.value = localidad.id;
                    option.textContent = localidad.nombre;
                    localidadSelect.appendChild(option);
                });
            });

        fetch(url2 + '?municipio_id=' + localidadId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_fk_asentamiento');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (asentamiento) {
                    var option = document.createElement('option');
                    option.value = asentamiento.id;
                    option.textContent = asentamiento.nombre;
                    localidadSelect.appendChild(option);
                });
            });
    });

    document.getElementById('id_fk_departamento').addEventListener('change', function () {
        var url = ajaxLoadLocalidadesUrl;  // Obtén la URL de la vista
        var departamentodId = this.options[this.selectedIndex].getAttribute('data-departamento-id');;  // Obtén el ID de la provincia seleccionada
        var url2 = ajaxLoadAsentameintosUrl;  // Obtén la URL de la vista
        fetch(url + '?departamento_id=' + departamentodId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_fk_localidad');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (localidad) {
                    var option = document.createElement('option');
                    option.value = localidad.id;
                    option.textContent = localidad.nombre;
                    localidadSelect.appendChild(option);
                });
            });

        fetch(url2 + '?departamento_id=' + departamentodId)
            .then(response => response.json())
            .then(data => {
                var localidadSelect = document.getElementById('id_fk_asentamiento');
                localidadSelect.innerHTML = '';  // Limpia el campo de municipios

                data.forEach(function (asentamiento) {
                    var option = document.createElement('option');
                    option.value = asentamiento.id;
                    option.textContent = asentamiento.nombre;
                    localidadSelect.appendChild(option);
                });
            });
    });

});


$(document).ready(function () {
    $('#id_nacionalidad').select2();
});

id_foto.onchange = (evt) => {
    const [file] = id_foto.files;
    if (file) {
        blah.src = URL.createObjectURL(file);
    }
};