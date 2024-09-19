const provinciaSelect = document.getElementById('id_provincia');
const municipioSelect = document.getElementById('id_municipio');
const localidadSelect = document.getElementById('id_localidad');


provinciaSelect.addEventListener('change', async function () {
    await cargarOpciones(`${ajaxLoadMunicipiosUrl}?provincia_id=${this.value}`, municipioSelect);
});

municipioSelect.addEventListener('change', async function () {
    await cargarOpciones(`${ajaxLoadLocalidadesUrl}?municipio_id=${this.value}`, localidadSelect);
});

async function cargarOpciones(url, select) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        select.innerHTML = '';

        data.forEach(item => crearOpcion(item, select));
    } catch (error) {
        console.error('Error al cargar opciones:', error);
    }
}

function crearOpcion({ id, nombre, nombre_region }, select) {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = nombre || nombre_region;
    select.appendChild(option);
}

$(document).ready(function () {
    $('#id_referente').select2();
});