document.addEventListener("DOMContentLoaded", function () {
    const addFirmanteButton = document.getElementById("add-firmante");
    const firmantesContainer = document.getElementById("firmantes-container");
    const totalForms = document.querySelector("#id_firmantes-TOTAL_FORMS");
    const tipoEntidadSelect = document.getElementById("id_tipo_entidad");
    const provinciaSelect = document.getElementById("id_provincia");
    const municipioSelect = document.getElementById("id_municipio");
    const localidadSelect = document.getElementById("id_localidad");
    const subtipoEntidadSelect = document.getElementById("id_subtipo_entidad");
    if (provinciaSelect) {
        provinciaSelect.addEventListener("change", async function () {
            await cargarOpciones(
            `${ajaxLoadMunicipiosUrl}?provincia_id=${this.value}`,
            "municipio"
            ).then(async () => {
            await cargarOpciones(
                `${ajaxLoadLocalidadesUrl}?municipio_id=${municipioSelect.options[0].value}`,
                "localidad"
            );
            });
        });
        }

        if (municipioSelect) {
        municipioSelect.addEventListener("change", async function () {
            await cargarOpciones(
            `${ajaxLoadLocalidadesUrl}?municipio_id=${this.value}`,
            "localidad"
            );
        });
        }

        async function cargarOpciones(url, select) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            if (select === "municipio") {
            municipioSelect.innerHTML = "";
            localidadSelect.innerHTML = "";
            data.forEach((item) => crearOpcion(item, municipioSelect));
            }

            if (select === "localidad") {
            localidadSelect.innerHTML = "";
            data.forEach((item) => crearOpcion(item, localidadSelect));
            }
        } catch (error) {
            console.error("Error al cargar opciones:", error);
        }
    }

    function crearOpcion({ id, nombre, nombre_region }, select) {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = nombre || nombre_region;
        select.appendChild(option);
    }



    subtipoEntidadSelect.innerHTML = "";

    function RenderSubtipoEntidad()
    {
        subtipoEntidadSelect.innerHTML = "";        
        const tipoEntidadId = this.value ? this.value : tipoEntidadSelect.value;
        fetch(`/organizaciones/subtipos-entidad/ajax/?tipo_entidad=${tipoEntidadId}`, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then(result => {
            result.forEach(subtipo => {
                const option = document.createElement("option");
                option.value = subtipo.id;
                option.textContent = subtipo.text;
                subtipoEntidadSelect.appendChild(option);
            });
        })
        .catch(error => console.error("Error al cargar subintervenciones:", error));
    }

    RenderSubtipoEntidad();

    if (tipoEntidadSelect) {
        tipoEntidadSelect.addEventListener("change", function () {
            RenderSubtipoEntidad();
        });
    }

});