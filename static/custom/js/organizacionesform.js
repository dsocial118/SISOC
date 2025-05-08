$(document).ready(function () {
    const tipoOrganizacion = document.querySelector("#id_tipo_organizacion");
    const juridicaForm = document.querySelector("#juridica-form");
    const eclesiasticaForm = document.querySelector("#eclesiastica-form");
    const hechoForm = document.querySelector("#hecho-form");

    // Función para mostrar/ocultar formularios
    function oculatarmostrarFormulario() {
        const selectedValue = tipoOrganizacion.value;
        juridicaForm.classList.add("d-none");
        eclesiasticaForm.classList.add("d-none");
        hechoForm.classList.add("d-none");


        if (selectedValue === "1") {
            juridicaForm.classList.remove("d-none");
        } else if (selectedValue === "2") {
            eclesiasticaForm.classList.remove("d-none");
        } else if (selectedValue === "3") {
            hechoForm.classList.remove("d-none");
        }
    }

    // Escuchar cambios en el campo tipo_organizacion
    tipoOrganizacion.addEventListener("change", toggleForms);

    // Inicializar la visibilidad de los formularios
    oculatarmostrarFormulario();
});
