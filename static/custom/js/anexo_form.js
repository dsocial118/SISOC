document.addEventListener("DOMContentLoaded", function () {
    const tipoPersonaFields = document.querySelectorAll("input[name='tipo_persona']");
    const juridicaFields = document.querySelectorAll(".juridica-field");
    const humanaFields = document.querySelectorAll(".humana-field");
    const stepTriggers = document.querySelectorAll('.step-trigger');
    const steps = document.querySelectorAll('.step');
    const stepContents = document.querySelectorAll('.step-content');
    const continueButton = document.getElementById('continueButton');

    function toggleFields() {
        const selectedTipoPersona = document.querySelector("input[name='tipo_persona']:checked").value;

        if (selectedTipoPersona === 'juridica') {
            juridicaFields.forEach(field => field.style.display = "");
            humanaFields.forEach(field => field.style.display = "none");
        } else {
            juridicaFields.forEach(field => field.style.display = "none");
            humanaFields.forEach(field => field.style.display = "");
        }
    }

    function handleStepClick(event) {
        document.querySelectorAll('.step').forEach(step => step.classList.remove('active'));

        const clickedStep = event.currentTarget.closest('.step');
        clickedStep.classList.add('active');

        const stepIndex = Array.from(document.querySelectorAll('.step')).indexOf(clickedStep) + 1;

        document.querySelectorAll('.step-content').forEach((content, index) => {
            if (index + 1 === stepIndex) {
                content.style.display = 'block'; // Mostrar contenido correspondiente
            } else {
                content.style.display = 'none'; // Ocultar otros contenidos
            }
        });
    }

    function handleContinueClick() {
        const activeStepIndex = Array.from(steps).findIndex(step => step.classList.contains('active'));

        if (activeStepIndex < steps.length - 1) {
            const nextStep = steps[activeStepIndex + 1];

            steps.forEach(step => step.classList.remove('active'));
            nextStep.classList.add('active');

            stepContents.forEach((content, index) => {
                content.style.display = index === activeStepIndex + 1 ? 'block' : 'none';
            });
        } else {
            const form = document.querySelector('form');
            if (form) {
                form.submit();
            } else {
                console.warn('No se encontró el formulario para enviar.');
            }
        }
    }


    // Steps
    stepTriggers.forEach(trigger => {
        trigger.addEventListener('click', handleStepClick);
    });
    continueButton.addEventListener('click', handleContinueClick);


    // Personeria
    tipoPersonaFields.forEach(field => field.addEventListener("change", toggleFields));
    toggleFields();
});


document.getElementById('presupuesto_select_tipo_actividad').addEventListener('change', function () {
    const selectedValue = this.selectedIndex;

    const bienesSelect = document.getElementById('presupuesto_select_bienes');
    const opciones = bienesSelect.querySelectorAll('option');

    opciones.forEach(opcion => {
        if (opcion.classList.contains(`tipo${selectedValue}`)) {
            opcion.style.display = 'block';
        } else {
            opcion.style.display = 'none';
        }
    });

    bienesSelect.value = '';
});

document.getElementById('submitForm').addEventListener('click', function () {
    const tipo_actividad = document.getElementById('presupuesto_select_tipo_actividad').value;
    const bienes = document.getElementById('presupuesto_select_bienes').value;
    const nombre = document.getElementById('presupuesto_nombre').value;
    const cantidad = document.getElementById('presupuesto_cantidad').value;
    const costo = document.getElementById('presupuesto_costo').value;

    // Crear una nueva fila
    const newRow = document.createElement('tr');

    // Crear celdas y agregarles el contenido
    const cellTipoActividad = document.createElement('td');
    cellTipoActividad.textContent = tipo_actividad;
    newRow.appendChild(cellTipoActividad);

    const cellBienes = document.createElement('td');
    cellBienes.textContent = bienes;
    newRow.appendChild(cellBienes);

    const cellNombre = document.createElement('td');
    cellNombre.textContent = nombre;
    newRow.appendChild(cellNombre);

    const cellCantidad = document.createElement('td');
    cellCantidad.textContent = cantidad;
    newRow.appendChild(cellCantidad);

    const cellCosto = document.createElement('td');
    cellCosto.textContent = costo;
    newRow.appendChild(cellCosto);

    // Agregar la nueva fila al cuerpo de la tabla
    document.getElementById('presupuestos').appendChild(newRow);


    // TODO: Aca hay que hacer que se creen filas con la informacoin del form


    $('#formModal').modal('hide');
});
