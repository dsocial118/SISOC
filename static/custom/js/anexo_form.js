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

    // Presupuesto
    document.getElementById('formularioModal').addEventListener('submit', function(event) {
        event.preventDefault();
    
        const tipo_actividad = document.getElementById('tipo_actividad').value;
        const bienes = document.getElementById('bienes').value;
        const nombre = document.getElementById('nombre').value;
        const cantidad = document.getElementById('cantidad').value;
        const costo = document.getElementById('costo').value;

    
        const modal = bootstrap.Modal.getInstance(document.getElementById('exampleModal'));
        
        const opcionesBienesServicios = {
            "1": ["Asistencia técnica específica a través de RRHH"],
            "2": ["Máquinas", "Herramientas", "Insumos"],
            "3": ["Máquinas", "Herramientas", "Conectividad"],
            "4": ["Entrega directa textiles"],
            "5": [
                "Asesoría Contable y Asesoría Jurídica",
                "Asesoría en Administración y Costos",
                "Asesoría y acompañamiento en diseño e inscripción de marca",
                "Asistencia en la confección de documentación y certificación de productos"
            ],
            "6": [
                "Asesoría en redes sociales y Plataformas de Venta",
                "Asesoría en Marketing digital (Foto Producto - Diseño de Catálogos online)"
            ],
            "7": [
                "Acompañamiento en técnicas de venta y oratoria",
                "Acompañamiento en armado de stands y vidrieras"
            ],
            "8": ["Acceso a nuevos mercados", "Participación en ferias y mercados"],
            "9": ["Equipamiento", "Insumos", "Gastos operativos", "Recursos humanos"],
            "10": [
                "Máquinas, Herramientas y Equipamiento",
                "Insumos e Indumentaria",
                "Asistencia técnica",
                "Transporte",
                "Infraestructura y equipamiento"
            ],
            "11": [],
            "12": [],
            "13": []
        };
        document.getElementById('tipo_actividad').addEventListener('change', function() {
            const tipoActividadSeleccionada = this.value;
            const bienesSelect = document.getElementById('bienes');
        
            // Limpiar las opciones actuales
            bienesSelect.innerHTML = '<option selected></option>';
        
            // Obtener las opciones de bienes/servicios correspondientes
            const opciones = opcionesBienesServicios[tipoActividadSeleccionada];
        
            // Verificar si hay opciones disponibles
            if (opciones && opciones.length > 0) {
                // Añadir cada opción al select de bienes
                opciones.forEach(opcion => {
                    const optionElement = document.createElement('option');
                    optionElement.value = opcion;
                    optionElement.textContent = opcion;
                    bienesSelect.appendChild(optionElement);
                });
            }
        });
        
        modal.hide();
        
    });
});


