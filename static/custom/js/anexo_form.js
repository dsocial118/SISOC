document.addEventListener("DOMContentLoaded", function() {
    const tipoPersonaFields = document.querySelectorAll("input[name='tipo_persona']");
    const juridicaFields = document.querySelectorAll(".juridica-field");
    const humanaFields = document.querySelectorAll(".humana-field");

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

    tipoPersonaFields.forEach(field => field.addEventListener("change", toggleFields));
    toggleFields();  // Llama una vez al cargar la página
});
