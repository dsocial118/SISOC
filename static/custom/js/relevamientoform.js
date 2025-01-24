const selectElements = [
    { select: "id_servicio_por_turnos", inputs: ["id_cantidad_turnos"], condition: conditionBoolean },
    { select: "id_tipo_espacio_fisico", inputs: ["id_espacio_fisico_otro"], condition: conditionOtro },
    { select: "id_abastecimiento_agua", inputs: ["id_abastecimiento_agua_otro"], condition: conditionOtro },
    { select: "id_gestion_quejas", inputs: ["id_gestion_quejas_otro"], condition: conditionOtro },
    { select: "id_tiene_sanitarios", inputs: ["id_desague_hinodoro"], condition: conditionBoolean },
    { select: "id_recibe_donaciones_particulares", inputs: ["id_frecuencia_donaciones_particulares", "id_recursos_donaciones_particulares"], condition: conditionBoolean },
    { select: "id_recibe_estado_nacional", inputs: ["id_frecuencia_estado_nacional", "id_recursos_estado_nacional"], condition: conditionBoolean },
    { select: "id_recibe_estado_provincial", inputs: ["id_frecuencia_estado_provincial", "id_recursos_estado_provincial"], condition: conditionBoolean },
    { select: "id_recibe_estado_municipal", inputs: ["id_frecuencia_estado_municipal", "id_recursos_estado_municipal"], condition: conditionBoolean },
    { select: "id_recibe_otros", inputs: ["id_frecuencia_otros", "id_recursos_otros"], condition: conditionBoolean },
    { 
        select: "id_comedor_merendero", 
        inputs: [
            "id_insumos_organizacion",
            "id_tipo_insumo",
            "id_frecuencia_insumo",
            "id_veces_recibio_insumos_2024",
            "id_tecnologia",
            "id_servicio_internet",
            "id_acceso_comedor",
            "id_distancia_transporte",
            "id_zona_inundable",
            "id_actividades_jardin_maternal",
            "id_actividades_jardin_infantes",
            "id_apoyo_escolar",
            "id_alfabetizacion_terminalidad",
            "id_capacitaciones_talleres",
            "id_promocion_salud",
            "id_actividades_discapacidad",
            "id_necesidades_alimentarias",
            "id_actividades_recreativas",
            "id_actividades_culturales",
            "id_emprendimientos_productivos",
            "id_actividades_religiosas",
            "id_actividades_huerta",
            "id_espacio_huerta",
            "id_otras_actividades",
            "id_cuales_otras_actividades",
        ], 
        condition: conditionBoolean },
        { 
            select: "id_insumos_organizacion", 
            inputs: [
                "id_frecuencia_otros", "id_tipo_insumo",
                "id_frecuencia_insumo",
                "id_veces_recibio_insumos_2024",
        ],
        condition: conditionBoolean },
    { select: "id_actividades_huerta", inputs: ["id_espacio_huerta"], condition: conditionBoolean },
    { select: "id_otras_actividades", inputs: ["id_cuales_otras_actividades"], condition: conditionBoolean },
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

function setupInputs() {
    selectElements.forEach(({ select, inputs, condition }) => {
        const selectElement = document.getElementById(select);

        initializeToggle(selectElement, inputs, condition);
        addToggleEvent(selectElement, inputs, condition);
    });
}

function setupReferenteInput() {
    selectElement = document.getElementById("id_responsable_es_referente");
    inputs = [
        "id_nombre",
        "id_apellido",
        "id_mail",
        "id_celular",
        "id_documento",
        "id_funcion"
    ]
    inputs.forEach(inputId => {
        const inputElement = document.getElementById(inputId);
        if (conditionBoolean(selectElement)) {
            inputElement.disabled = true;
            setResponsableValues()
        } else {
            inputElement.disabled = false;
        }
    });

    selectElement.addEventListener("change", function () {
        inputs.forEach(inputId => {
            const inputElement = document.getElementById(inputId);
            if (conditionBoolean(selectElement)) {
                inputElement.disabled = true;
                setReferenteValues()
            } else {
                inputElement.disabled = false;
            }
        });
    });

    function setReferenteValues() {
        document.getElementById("id_nombre").value = referente.nombre || ''
        document.getElementById("id_apellido").value = referente.apellido || ''
        document.getElementById("id_mail").value = referente.mail || ''
        document.getElementById("id_celular").value = referente.celular || ''
        document.getElementById("id_documento").value = referente.documento || ''
        document.getElementById("id_funcion").value = referente.funcion || ''
    }

    function setResponsableValues() {
        document.getElementById("id_nombre").value = responsable.nombre || ''
        document.getElementById("id_apellido").value = responsable.apellido || ''
        document.getElementById("id_mail").value = responsable.mail || ''
        document.getElementById("id_celular").value = responsable.celular || ''
        document.getElementById("id_documento").value = responsable.documento || ''
        document.getElementById("id_funcion").value = responsable.funcion || ''
    }
    setResponsableValues()
}

document.addEventListener("DOMContentLoaded", function () {
    setupInputs();
    setupReferenteInput()
});