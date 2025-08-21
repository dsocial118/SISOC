const provinciaSelect = document.getElementById("id_provincia");
const municipioSelect = document.getElementById("id_municipio");
const localidadSelect = document.getElementById("id_localidad");

function confirmSubmit() {
  return confirm("¿Estás seguro de que deseas guardar el comedor?");
}

if (provinciaSelect) {
  provinciaSelect.addEventListener("change", async function () {
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
  
  // Array para almacenar todos los archivos seleccionados
  let selectedFiles = [];

    const addImagesBtn = document.getElementById("addImagesBtn");
    const imagenesInput = document.getElementById("imagenesInput");
    const selectedImagesInfo = document.getElementById("selectedImagesInfo");
    const imageCount = document.getElementById("imageCount");
    const imagePreviewContainer = document.getElementById("imagePreviewContainer");

  // FUNCIONALIDAD PARA IMÁGENES EXISTENTES
  function setupExistingImages() {
    
    const checkboxes = document.querySelectorAll(".checkbox-eliminar-custom");
    const deleteButtons = document.querySelectorAll(".btn-eliminar-custom");

    // Configurar checkboxes
    checkboxes.forEach((checkbox, index) => {
      
      checkbox.addEventListener("change", function () {
        
        const imageId = this.getAttribute("data-image-id");
        const imageItem = this.closest('.imagen-existente') || document.querySelector(`[data-image-id="${imageId}"]`);
        
        if (imageItem) {
          toggleImageElimination(imageItem, this.checked);
          updateDeleteButtonText(imageItem, this.checked);
        }
      });
    });

    // Configurar botones de eliminar
    deleteButtons.forEach((button, index) => {
      
      button.addEventListener("click", function (e) {
        e.preventDefault();
        
        const imageItem = this.closest(".imagen-existente");
        const checkbox = imageItem ? imageItem.querySelector(".checkbox-eliminar-custom") : null;

        if (checkbox) {
          checkbox.checked = !checkbox.checked;

          // Disparar evento change manualmente
          const event = new Event('change', { bubbles: true });
          checkbox.dispatchEvent(event);
        }
      });
    });
  }

  function toggleImageElimination(imageItem, isMarked) {
    
    if (!imageItem) {
      return;
    }

    const overlay = imageItem.querySelector(".overlay-eliminar");

    if (isMarked) {
      // Marcar para eliminar
      imageItem.classList.add("imagen-eliminada");
      if (overlay) {
        overlay.classList.remove("d-none");
      }
    } else {
      // Desmarcar
      imageItem.classList.remove("imagen-eliminada");
      if (overlay) {
        overlay.classList.add("d-none");
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
      } else {
        deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
        deleteButton.style.backgroundColor = '#e74c3c'; // Rojo
        deleteButton.title = 'Marcar para eliminar';
      }
    }
  }

  // FUNCIONALIDAD PARA CARGAR IMÁGENES EXISTENTES
  function loadExistingImages() {
    
    const imageContainers = document.querySelectorAll('.imagen-thumbnail-container');
    
    imageContainers.forEach((container, index) => {
      const imageUrl = container.getAttribute('data-image-url');
      const placeholder = container.querySelector('.preview-placeholder');
      
      if (imageUrl && placeholder) {
        
        // Crear elemento img
        const img = document.createElement('img');
        img.className = 'imagen-thumbnail';
        img.alt = 'Imagen del comedor';
        img.src = imageUrl;
        
        img.onload = function() {
          placeholder.replaceWith(img);
        };
        
        img.onerror = function() {
          placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
          placeholder.style.color = '#e74c3c';
          placeholder.title = 'Error al cargar imagen';
        };
        
        // Timeout de seguridad (10 segundos)
        setTimeout(() => {
          if (placeholder.parentNode === container) {
            placeholder.innerHTML = '<i class="fas fa-clock"></i>';
            placeholder.style.color = '#f39c12';
            placeholder.title = 'Imagen no disponible';
          }
        }, 10000);
        
      } else {
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
    
    // Event listener para el botón de agregar imágenes
    addImagesBtn.addEventListener("click", function () {
      imagenesInput.click();
    });

    // Event listener para cuando se seleccionan archivos
    imagenesInput.addEventListener("change", function () {
      
      const files = Array.from(this.files);
      
      // IMPORTANTE: Concatenar archivos en lugar de reemplazar
      selectedFiles = selectedFiles.concat(files);
      
      // Actualizar la vista
      updateImageDisplay();
      updateFileInput();
    });

    function updateImageDisplay() {
      
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
          
          // Verificar que el archivo sea una imagen válida
          if (!file.type.startsWith('image/')) {
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
                placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                placeholder.style.color = '#dc3545';
              };
            };
            
            reader.onerror = function() {
              placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
              placeholder.style.color = '#dc3545';
            };
            
            try {
              reader.readAsDataURL(file);
            } catch (error) {
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
      } catch (error) {
      }
    }

    function removeFileByIndex(index) {
      
      // Encontrar el archivo por nombre para mayor seguridad
      const previewElement = document.querySelector(`[data-index="${index}"]`);
      if (previewElement) {
        const fileName = previewElement.querySelector('.preview-info-content')?.textContent;
        
        if (fileName) {
          // Buscar el archivo por nombre
          const fileIndex = selectedFiles.findIndex(file => file.name === fileName);
          if (fileIndex !== -1) {
            selectedFiles.splice(fileIndex, 1);
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
      }
    }

    // Función global para eliminar imagen (compatibilidad)
    window.removeImage = function (index) {
      removeFileByIndex(index);
    };
  }

  // Inicializar funcionalidad de imágenes existentes
  setupExistingImages();
  
  // Cargar imágenes existentes
  loadExistingImages();
  
  // Inicializar funcionalidad de foto de legajo
  setupFotoLegajo();
});

// FUNCIONALIDAD PARA FOTO DE LEGAJO
function setupFotoLegajo() {
  
  // Cargar foto de legajo existente
  const fotoThumbnailContainer = document.querySelector('.foto-thumbnail-container');
  if (fotoThumbnailContainer) {
    cargarFotoLegajoExistente(fotoThumbnailContainer);
  }
  
  // Configurar preview para nueva foto
  const fotoLegajoInput = document.getElementById('id_foto_legajo');
  if (fotoLegajoInput) {
    fotoLegajoInput.addEventListener('change', function() {
      const file = this.files[0];
      
      if (file) {
        mostrarPreviewFotoLegajo(file);
      } else {
        ocultarPreviewFotoLegajo();
      }
    });
  }
}

function cargarFotoLegajoExistente(container) {
  const imageUrl = container.getAttribute('data-image-url');
  const placeholder = container.querySelector('.preview-placeholder');
  
  if (imageUrl && placeholder) {
    
    placeholder.classList.add('loading');
    
    const img = document.createElement('img');
    img.alt = 'Foto de legajo';
    img.src = imageUrl;
    
    img.onload = function() {
      placeholder.replaceWith(img);
    };
    
    img.onerror = function() {
      placeholder.classList.remove('loading');
      placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i><br><small>Error al cargar</small>';
      placeholder.style.background = '#dc3545';
    };
    
    setTimeout(() => {
      if (placeholder.parentNode === container) {
        placeholder.classList.remove('loading');
        placeholder.innerHTML = '<i class="fas fa-clock"></i><br><small>Tiempo agotado</small>';
        placeholder.style.background = '#ffc107';
        placeholder.style.color = '#000';
      }
    }, 10000);
  }
}

function mostrarPreviewFotoLegajo(file) {
  
  if (!file.type.startsWith('image/')) {
    alert('Por favor selecciona un archivo de imagen válido.');
    return;
  }
  
  const previewContainer = document.getElementById('fotoLegajoPreviewContainer');
  const previewImg = document.getElementById('fotoLegajoPreview');
  const nombreElement = document.getElementById('fotoLegajoNombre');
  const sizeElement = document.getElementById('fotoLegajoSize');
  
  if (previewContainer && previewImg && nombreElement && sizeElement) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
      previewImg.src = e.target.result;
      nombreElement.textContent = file.name;
      sizeElement.textContent = formatFileSize(file.size);
      previewContainer.classList.remove('d-none');
    };
    
    reader.onerror = function() {
      alert('Error al leer el archivo seleccionado.');
    };
    
    reader.readAsDataURL(file);
  }
}

function ocultarPreviewFotoLegajo() {
  const previewContainer = document.getElementById('fotoLegajoPreviewContainer');
  if (previewContainer) {
    previewContainer.classList.add('d-none');
  }
}

function removerPreviewFotoLegajo() {
  const fotoLegajoInput = document.getElementById('id_foto_legajo');
  if (fotoLegajoInput) {
    fotoLegajoInput.value = '';
  }
  ocultarPreviewFotoLegajo();
}

function ampliarFotoLegajo(url, nombre) {
  
  const modalImg = document.getElementById('fotoLegajoPrincipal');
  const nombreModal = document.getElementById('nombreArchivoLegajo');
  
  if (modalImg && nombreModal) {
    modalImg.src = url;
    nombreModal.textContent = nombre || 'foto_legajo.jpg';
    
    const modal = new bootstrap.Modal(document.getElementById('fotoLegajoModal'));
    modal.show();
  }
}

function descargarFotoLegajo() {
  const modalImg = document.getElementById('fotoLegajoPrincipal');
  const nombreModal = document.getElementById('nombreArchivoLegajo');
  
  if (modalImg && modalImg.src) {
    const link = document.createElement('a');
    link.href = modalImg.src;
    link.download = nombreModal.textContent || 'foto_legajo.jpg';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

// Funciones globales para compatibilidad con HTML
window.ampliarFotoLegajo = ampliarFotoLegajo;
window.descargarFotoLegajo = descargarFotoLegajo;
window.removerPreviewFotoLegajo = removerPreviewFotoLegajo;
