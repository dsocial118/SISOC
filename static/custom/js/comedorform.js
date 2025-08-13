const provinciaSelect = document.getElementById("id_provincia");
const municipioSelect = document.getElementById("id_municipio");
const localidadSelect = document.getElementById("id_localidad");

function confirmSubmit() {
  return confirm("¿Estás seguro de que deseas guardar el comedor?");
}

if (provinciaSelect) {
  provinciaSelect.addEventListener("change", async function () {
    console.log("Provincia:", this.value);
    await cargarOpciones(
      `${ajaxLoadMunicipiosUrl}?provincia_id=${this.value}`,
      "municipio"
    ).then(async () => {
      await cargarOpciones(
        `${ajaxLoadLocalidadesUrl}?municipio_id=${municipioSelect.options[0].value}`,
        "localidad"
      );
    });
  });
}

if (municipioSelect) {
  municipioSelect.addEventListener("change", async function () {
    await cargarOpciones(
      `${ajaxLoadLocalidadesUrl}?municipio_id=${this.value}`,
      "localidad"
    );
  });
}

async function cargarOpciones(url, select) {
  try {
    const response = await fetch(url);
    const data = await response.json();
    if (select === "municipio") {
      municipioSelect.innerHTML = "";
      localidadSelect.innerHTML = "";
      data.forEach((item) => crearOpcion(item, municipioSelect));
    }

    if (select === "localidad") {
      localidadSelect.innerHTML = "";
      data.forEach((item) => crearOpcion(item, localidadSelect));
    }
  } catch (error) {
    console.error("Error al cargar opciones:", error);
  }
}

function crearOpcion({ id, nombre, nombre_region }, select) {
  const option = document.createElement("option");
  option.value = id;
  option.textContent = nombre || nombre_region;
  select.appendChild(option);
}

// FUNCIONALIDAD DE IMÁGENES
document.addEventListener("DOMContentLoaded", function () {
  console.log("Iniciando funcionalidad de imágenes...");
  
  // Array para almacenar todos los archivos seleccionados
  let selectedFiles = [];

  const addImagesBtn = document.getElementById("addImagesBtn");
  const imagenesInput = document.getElementById("imagenesInput");
  const selectedImagesInfo = document.getElementById("selectedImagesInfo");
  const imageCount = document.getElementById("imageCount");
  const imagePreviewContainer = document.getElementById("imagePreviewContainer");

  console.log("Elementos encontrados:", {
    addImagesBtn: !!addImagesBtn,
    imagenesInput: !!imagenesInput,
    selectedImagesInfo: !!selectedImagesInfo,
    imageCount: !!imageCount,
    imagePreviewContainer: !!imagePreviewContainer
  });

  // FUNCIONALIDAD PARA IMÁGENES EXISTENTES
  function setupExistingImages() {
    console.log("Configurando imágenes existentes...");
    
    const checkboxes = document.querySelectorAll(".checkbox-eliminar-custom");
    const deleteButtons = document.querySelectorAll(".btn-eliminar-custom");

    console.log(`Encontrados ${checkboxes.length} checkboxes y ${deleteButtons.length} botones`);

    // Configurar checkboxes
    checkboxes.forEach((checkbox, index) => {
      console.log(`Configurando checkbox ${index}:`, checkbox.id);
      
      checkbox.addEventListener("change", function () {
        console.log("Checkbox cambiado:", this.id, "Checked:", this.checked);
        
        const imageId = this.getAttribute("data-image-id");
        const imageItem = this.closest('.imagen-existente') || document.querySelector(`[data-image-id="${imageId}"]`);
        
        if (imageItem) {
          toggleImageElimination(imageItem, this.checked);
          updateDeleteButtonText(imageItem, this.checked);
        } else {
          console.error("No se encontró el elemento imagen con ID:", imageId);
        }
      });
    });

    // Configurar botones de eliminar
    deleteButtons.forEach((button, index) => {
      console.log(`Configurando botón ${index}`);
      
      button.addEventListener("click", function (e) {
        e.preventDefault();
        console.log("Botón de eliminar clickeado");
        
        const imageItem = this.closest(".imagen-existente");
        const checkbox = imageItem ? imageItem.querySelector(".checkbox-eliminar-custom") : null;

        if (checkbox) {
          console.log("Cambiando estado del checkbox desde:", checkbox.checked, "a:", !checkbox.checked);
          checkbox.checked = !checkbox.checked;
          
          // Disparar evento change manualmente
          const event = new Event('change', { bubbles: true });
          checkbox.dispatchEvent(event);
        } else {
          console.error("No se encontró el checkbox asociado al botón");
        }
      });
    });
  }

  function toggleImageElimination(imageItem, isMarked) {
    console.log("Toggle eliminación:", isMarked);
    
    if (!imageItem) {
      console.error("imageItem es null");
      return;
    }

    const overlay = imageItem.querySelector(".overlay-eliminar");

    if (isMarked) {
      // Marcar para eliminar
      imageItem.classList.add("imagen-eliminada");
      if (overlay) {
        overlay.classList.remove("d-none");
        console.log("Overlay mostrado");
      }
    } else {
      // Desmarcar
      imageItem.classList.remove("imagen-eliminada");
      if (overlay) {
        overlay.classList.add("d-none");
        console.log("Overlay ocultado");
      }
    }
  }

  function updateDeleteButtonText(imageItem, isMarked) {
    const deleteButton = imageItem ? imageItem.querySelector(".btn-eliminar-custom") : null;
    
    if (deleteButton) {
      if (isMarked) {
        deleteButton.innerHTML = '<i class="fas fa-undo"></i>';
        deleteButton.style.backgroundColor = '#27ae60'; // Verde
        deleteButton.title = 'Desmarcar para eliminar';
        console.log("Botón cambiado a verde (deshacer)");
      } else {
        deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
        deleteButton.style.backgroundColor = '#e74c3c'; // Rojo
        deleteButton.title = 'Marcar para eliminar';
        console.log("Botón cambiado a rojo (eliminar)");
      }
    }
  }

  // FUNCIONALIDAD PARA CARGAR IMÁGENES EXISTENTES
  function loadExistingImages() {
    console.log("Cargando imágenes existentes...");
    
    const imageContainers = document.querySelectorAll('.imagen-thumbnail-container');
    console.log(`Encontrados ${imageContainers.length} contenedores de imágenes existentes`);
    
    imageContainers.forEach((container, index) => {
      const imageUrl = container.getAttribute('data-image-url');
      const placeholder = container.querySelector('.preview-placeholder');
      
      if (imageUrl && placeholder) {
        console.log(`Cargando imagen ${index}:`);
        console.log(`  - URL: ${imageUrl}`);
        console.log(`  - URL absoluta: ${window.location.origin}${imageUrl}`);
        
        // Crear elemento img
        const img = document.createElement('img');
        img.className = 'imagen-thumbnail';
        img.alt = 'Imagen del comedor';
        img.src = imageUrl;
        
        img.onload = function() {
          console.log(`Imagen ${index} cargada exitosamente`);
          placeholder.replaceWith(img);
        };
        
        img.onerror = function() {
          console.error(`Error al cargar imagen ${index}: ${imageUrl}`);
          placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
          placeholder.style.color = '#e74c3c';
          placeholder.title = 'Error al cargar imagen';
        };
        
        // Timeout de seguridad (10 segundos)
        setTimeout(() => {
          if (placeholder.parentNode === container) {
            console.warn(`Timeout cargando imagen ${index}: ${imageUrl}`);
            placeholder.innerHTML = '<i class="fas fa-clock"></i>';
            placeholder.style.color = '#f39c12';
            placeholder.title = 'Imagen no disponible';
          }
        }, 10000);
        
      } else {
        console.warn(`Contenedor ${index} sin URL de imagen o placeholder`);
        if (placeholder) {
          placeholder.innerHTML = '<i class="fas fa-question-circle"></i>';
          placeholder.style.color = '#95a5a6';
          placeholder.title = 'URL no disponible';
        }
      }
    });
  }

  // FUNCIONALIDAD PARA NUEVAS IMÁGENES
  if (addImagesBtn && imagenesInput) {
    console.log("Configurando funcionalidad de nuevas imágenes...");
    
    // Event listener para el botón de agregar imágenes
    addImagesBtn.addEventListener("click", function () {
      console.log("Botón de agregar imágenes clickeado");
      imagenesInput.click();
    });

    // Event listener para cuando se seleccionan archivos
    imagenesInput.addEventListener("change", function () {
      console.log("Archivos seleccionados:", this.files.length);
      
      const files = Array.from(this.files);
      
      // IMPORTANTE: Concatenar archivos en lugar de reemplazar
      selectedFiles = selectedFiles.concat(files);
      
      console.log("Total de archivos después de agregar:", selectedFiles.length);
      
      // Actualizar la vista
      updateImageDisplay();
      updateFileInput();
    });

    function updateImageDisplay() {
      console.log("Actualizando display de imágenes, archivos:", selectedFiles.length);
      
      // Mostrar contador
      if (selectedFiles.length > 0) {
        selectedImagesInfo?.classList.remove("d-none");
        if (imageCount) imageCount.textContent = selectedFiles.length;
      } else {
        selectedImagesInfo?.classList.add("d-none");
      }

      // Limpiar contenedor de vistas previas
      if (imagePreviewContainer) {
        imagePreviewContainer.innerHTML = "";

        // Mostrar vista previa de cada imagen
        selectedFiles.forEach((file, index) => {
          console.log(`Procesando archivo ${index}: ${file.name}, tipo: ${file.type}`);
          
          // Verificar que el archivo sea una imagen válida
          if (!file.type.startsWith('image/')) {
            console.warn('Archivo no es una imagen:', file.name);
            return;
          }

          // Crear contenedor principal
          const previewDiv = document.createElement("div");
          previewDiv.className = "preview-nueva-imagen";
          previewDiv.setAttribute('data-index', index);

          // Crear placeholder inicial para la imagen
          const placeholder = document.createElement("div");
          placeholder.className = "preview-placeholder";
          placeholder.innerHTML = '<i class="fas fa-image"></i>';

          // Crear contenedor de información
          const infoDiv = document.createElement("div");
          infoDiv.className = "preview-info";
          
          infoDiv.innerHTML = `
            <div class="preview-info-content">${file.name}</div>
            <div class="preview-size">${formatFileSize(file.size)}</div>
            <div class="preview-status">
              <i class="fas fa-check-circle"></i>
              Seleccionada
            </div>
          `;

          // Crear botón eliminar
          const btnEliminar = document.createElement('button');
          btnEliminar.type = 'button';
          btnEliminar.className = 'btn-eliminar-preview';
          btnEliminar.innerHTML = '<i class="fas fa-times"></i>';
          btnEliminar.title = 'Eliminar imagen';
          btnEliminar.onclick = function() {
            console.log("Eliminando imagen en índice:", index);
            removeFileByIndex(index);
          };

          // Ensamblar el preview
          previewDiv.appendChild(placeholder);
          previewDiv.appendChild(infoDiv);
          previewDiv.appendChild(btnEliminar);

          // Agregar al contenedor
          imagePreviewContainer.appendChild(previewDiv);

          // Intentar cargar la imagen de forma asíncrona
          setTimeout(() => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
              console.log(`Imagen ${index} cargada exitosamente`);
              
              // Crear elemento img
              const img = document.createElement('img');
              img.className = 'preview-imagen';
              img.alt = 'Vista previa';
              img.src = e.target.result;
              
              // Reemplazar el placeholder con la imagen
              img.onload = function() {
                placeholder.replaceWith(img);
              };
              
              img.onerror = function() {
                console.warn('Error al mostrar la imagen:', file.name);
                placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                placeholder.style.color = '#dc3545';
              };
            };
            
            reader.onerror = function() {
              console.error('Error al leer el archivo:', file.name);
              placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
              placeholder.style.color = '#dc3545';
            };
            
            try {
              reader.readAsDataURL(file);
            } catch (error) {
              console.error('Error al procesar archivo:', error);
              placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
              placeholder.style.color = '#dc3545';
            }
          }, 100); // Pequeño delay para mejorar el rendimiento
        });
      }
    }

    function formatFileSize(bytes) {
      if (bytes === 0) return "0 Bytes";
      const k = 1024;
      const sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    function updateFileInput() {
      try {
        // Crear un nuevo DataTransfer para actualizar el input file
        const dt = new DataTransfer();
        selectedFiles.forEach((file) => {
          if (file && file instanceof File) {
            dt.items.add(file);
          }
        });
        imagenesInput.files = dt.files;
        console.log('Input file actualizado con', dt.files.length, 'archivos');
      } catch (error) {
        console.error('Error al actualizar input file:', error);
      }
    }

    function removeFileByIndex(index) {
      console.log("Eliminando imagen en índice:", index, "Total archivos:", selectedFiles.length);
      
      // Encontrar el archivo por nombre para mayor seguridad
      const previewElement = document.querySelector(`[data-index="${index}"]`);
      if (previewElement) {
        const fileName = previewElement.querySelector('.preview-info-content')?.textContent;
        
        if (fileName) {
          // Buscar el archivo por nombre
          const fileIndex = selectedFiles.findIndex(file => file.name === fileName);
          if (fileIndex !== -1) {
            selectedFiles.splice(fileIndex, 1);
            console.log(`Archivo ${fileName} eliminado. Archivos restantes:`, selectedFiles.length);
            updateImageDisplay();
            updateFileInput();
            return;
          }
        }
      }
      
      // Fallback al método original si no se encuentra por nombre
      if (index >= 0 && index < selectedFiles.length) {
        selectedFiles.splice(index, 1);
        updateImageDisplay();
        updateFileInput();
      } else {
        console.error('Índice inválido:', index, 'Archivos disponibles:', selectedFiles.length);
      }
    }

    // Función global para eliminar imagen (compatibilidad)
    window.removeImage = function (index) {
      removeFileByIndex(index);
    };
  } else {
    console.error("No se encontraron los elementos necesarios para nuevas imágenes");
  }

  // Inicializar funcionalidad de imágenes existentes
  setupExistingImages();
  
  // Cargar imágenes existentes
  loadExistingImages();
  
  console.log("Funcionalidad de imágenes inicializada correctamente");
});
