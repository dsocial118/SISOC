document.addEventListener("DOMContentLoaded", function () {
    configurarInputs();

    configurarAgregarPrestaciones();
});

function configurarAgregarPrestaciones() {
    document.getElementById('add-prestacion').addEventListener('click', function () {
        var formIdx = document.querySelectorAll('.prestacion-form').length;
        var newForm = document.querySelectorAll('.prestacion-form')[0].cloneNode(true);
        newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, formIdx);
        document.getElementById('prestaciones').appendChild(newForm);
    });
}

function configurarInputs() {
    const selectElements = [
        { select: "id_servicio_por_turnos", inputs: ["id_cantidad_turnos"], condition: conditionBoolean },
        { select: "id_tipo_espacio_fisico", inputs: ["id_espacio_fisico_otro"], condition: conditionOtro },
        { select: "id_tiene_sanitarios", inputs: ["id_desague_hinodoro"], condition: conditionBoolean },
        { select: "id_recibe_donaciones_particulares", inputs: ["id_frecuencia_donaciones_particulares", "id_recursos_donaciones_particulares"], condition: conditionBoolean },
        { select: "id_recibe_estado_nacional", inputs: ["id_frecuencia_estado_nacional", "id_recursos_estado_nacional"], condition: conditionBoolean },
        { select: "id_recibe_estado_provincial", inputs: ["id_frecuencia_estado_provincial", "id_recursos_estado_provincial"], condition: conditionBoolean },
        { select: "id_recibe_estado_municipal", inputs: ["id_frecuencia_estado_municipal", "id_recursos_estado_municipal"], condition: conditionBoolean },
        { select: "id_recibe_otros", inputs: ["id_frecuencia_otros", "id_recursos_otros"], condition: conditionBoolean }
    ];

    function toggleInput(selectElement, inputElement, condition) {
        if (condition(selectElement)) {
            inputElement.disabled = false;
        } else {
            inputElement.value = '';
            inputElement.disabled = true;
        }
    }

    function conditionBoolean(selectElement) {
        return selectElement.value === "True";
    }

    function conditionOtro(selectElement) {
        return selectElement.options[selectElement.selectedIndex].text === "Otro";
    }

    function initializeToggle(selectElement, inputElements, condition) {
        inputElements.forEach(inputId => {
            const inputElement = document.getElementById(inputId);
            toggleInput(selectElement, inputElement, condition);
        });
    }

    function addToggleEvent(selectElement, inputElements, condition) {
        selectElement.addEventListener("change", function () {
            initializeToggle(selectElement, inputElements, condition);
        });
    }

    selectElements.forEach(({ select, inputs, condition }) => {
        const selectElement = document.getElementById(select);
        initializeToggle(selectElement, inputs, condition);
        addToggleEvent(selectElement, inputs, condition);
    });
}
