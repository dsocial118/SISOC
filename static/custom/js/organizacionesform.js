$(document).ready(function () {

    const addFirmanteButton = document.getElementById("add-firmante");
    const firmantesContainer = document.getElementById("firmantes-container");
    const totalForms = document.querySelector("#id_firmantes-TOTAL_FORMS");

    addFirmanteButton.addEventListener("click", function () {
        const newForm = firmantesContainer.children[0].cloneNode(true);
        const formRegex = new RegExp(`-0-`, "g");
        Array.from(newForm.querySelectorAll("[name], [id], [for]")).forEach(function (element) {
            if (element.name) {
                element.name = element.name.replace(formRegex, `-${totalForms.value}-`);
            }
            if (element.id) {
                element.id = element.id.replace(formRegex, `-${totalForms.value}-`);
            }
            if (element.htmlFor) {
                element.htmlFor = element.htmlFor.replace(formRegex, `-${totalForms.value}-`);
            }
        });
        firmantesContainer.appendChild(newForm);
        totalForms.value = parseInt(totalForms.value) + 1;
    });

    firmantesContainer.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-firmante")) {
            // Verificar si hay más de un formulario antes de eliminar
            if (firmantesContainer.children.length > 1) {
                e.target.closest(".form-row").remove();
                totalForms.value = parseInt(totalForms.value) - 1;
            } else {
                alert("Debe haber al menos un firmante.");
            }
        }
    });

});