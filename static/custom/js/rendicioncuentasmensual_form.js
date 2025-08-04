document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("add-documentacion");
    const container = document.getElementById("documentacion-container");
    const removeButton = document.getElementById("remove-documentacion");

    addButton.addEventListener("click", function () {
        const firstItem = container.querySelector(".documentacion-item:last-child");
        const newItem = firstItem.cloneNode(true);
        const inputs = newItem.querySelectorAll("input");
        inputs.forEach(input => input.value = "");
        container.appendChild(newItem);
    });

    removeButton.addEventListener("click", function () {
        const items = container.querySelectorAll(".documentacion-item");
        if (items.length > 1) {
            items[items.length - 1].remove();
        } else {
            const inputs = items[0].querySelectorAll("input, textarea, select");
            inputs.forEach(input => input.value = "");
        }
    });


    container.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-existing-documentacion")) {
            const archivoId = event.target.getAttribute("data-id");
            if (confirm("¿Estás seguro de que deseas eliminar este archivo?")) {
                fetch(`/rendicioncuentasmensual/eliminar-archivo/${archivoId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert(data.message);
                            event.target.closest(".documentacion-edit-item").remove();
                        } else {
                            alert("Error al eliminar el archivo: " + data.message);
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        alert("Ocurrió un error al intentar eliminar el archivo.");
                    });
            }
        }
    });
});
