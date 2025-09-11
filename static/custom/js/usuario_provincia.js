// Validates image type (PNG or JPEG) before previewing and toggles provincial field.
document.addEventListener("DOMContentLoaded", function () {
  const checkbox = document.getElementById("id_es_usuario_provincial");
  const provinciaContainer = document.getElementById("provincia-container");

  function toggleProvinciaField() {
    if (checkbox.checked) {
      provinciaContainer.style.display = "block";
    } else {
      provinciaContainer.style.display = "none";
      const select = provinciaContainer.querySelector("select");
      if (select) select.selectedIndex = 0;
    }
  }

  if (checkbox && provinciaContainer) {
    toggleProvinciaField(); // Estado inicial
    checkbox.addEventListener("change", toggleProvinciaField);
  }

  // Imagen
  const imagenInput = document.getElementById("id_imagen");
  const imagenPreview = document.getElementById("blah");
  const label = document.getElementById("label_id_imagen");

  if (imagenInput && imagenPreview && label) {
    imagenInput.onchange = () => {
      const [file] = imagenInput.files;
      if (file) {
        if (["image/png", "image/jpeg"].includes(file.type)) {
          imagenPreview.src = URL.createObjectURL(file);
          label.innerText = "Cambiar imagen";
        } else {
          imagenInput.value = "";
          imagenPreview.src = "";
          alert("Solo se permiten imágenes PNG y JPEG.");
        }
      }
    };
  }
});
