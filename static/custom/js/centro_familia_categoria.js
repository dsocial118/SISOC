document.addEventListener("DOMContentLoaded", function () {
        const categoriaSelect = document.getElementById("id_categoria");
        const actividadSelect = document.getElementById("id_actividad");

        categoriaSelect.addEventListener("change", function () {
            const categoriaId = this.value;
            actividadSelect.innerHTML = '<option value="">Cargando...</option>';

            fetch(`/ajax/actividades/?categoria_id=${categoriaId}`)
                .then(response => response.json())
                .then(data => {
                    actividadSelect.innerHTML = '<option value="">Seleccione una actividad</option>';
                    data.forEach(item => {
                        const option = document.createElement("option");
                        option.value = item.id;
                        option.textContent = item.nombre;
                        actividadSelect.appendChild(option);
                    });
                });
        });
    });

