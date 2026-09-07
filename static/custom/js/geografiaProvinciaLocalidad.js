/**
 * Reutiliza el catálogo territorial para pares Provincia/Localidad que no
 * requieren seleccionar el municipio en el formulario.
 */
(function (window, document) {
    function replaceOptions(select, localidades, selectedValue) {
        select.innerHTML = "";
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "Seleccione una localidad";
        select.appendChild(empty);

        localidades.forEach((localidad) => {
            const option = document.createElement("option");
            option.value = localidad.id;
            option.textContent = localidad.nombre;
            option.selected = String(localidad.id) === String(selectedValue);
            select.appendChild(option);
        });
    }

    async function loadLocalidades(url, provincia, localidad, preserveValue) {
        const provinciaId = provincia.value;
        if (!provinciaId) {
            replaceOptions(localidad, [], "");
            return;
        }
        localidad.disabled = true;
        try {
            const response = await fetch(
                `${url}?provincia_id=${encodeURIComponent(provinciaId)}`,
                {
                    credentials: "same-origin",
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                }
            );
            if (!response.ok) throw new Error(`Error ${response.status}`);
            replaceOptions(localidad, await response.json(), preserveValue);
        } catch (error) {
            console.error("No se pudieron cargar las localidades.", error);
            replaceOptions(localidad, [], "");
        } finally {
            localidad.disabled = false;
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("form[data-localidades-url]").forEach((form) => {
            const url = form.dataset.localidadesUrl;
            form.querySelectorAll("[data-geografia-provincia]").forEach((provincia) => {
                const localidad = document.getElementById(provincia.dataset.geografiaProvincia);
                if (!localidad) return;
                const selectedValue = localidad.value;
                provincia.addEventListener("change", () => loadLocalidades(url, provincia, localidad, ""));
                if (provincia.value) loadLocalidades(url, provincia, localidad, selectedValue);
            });
        });
    });
}(window, document));
