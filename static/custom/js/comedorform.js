const provinciaSelect = document.getElementById('id_provincia');
const municipioSelect = document.getElementById('id_municipio');
const localidadSelect = document.getElementById('id_localidad');


function confirmSubmit() {
    return confirm("¿Estás seguro de que deseas guardar el comedor?");
}

provinciaSelect.addEventListener('change', async function () {
    console.log('Provincia:', this.value);
    await cargarOpciones(`${ajaxLoadMunicipiosUrl}?provincia_id=${this.value}`, "municipio").then(async () => {
        await cargarOpciones(`${ajaxLoadLocalidadesUrl}?municipio_id=${municipioSelect.options[0].value}`, "localidad");
    })

});

municipioSelect.addEventListener('change', async function () {
    await cargarOpciones(`${ajaxLoadLocalidadesUrl}?municipio_id=${this.value}`, "localidad");
});

async function cargarOpciones(url, select) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        if (select === "municipio") {
            municipioSelect.innerHTML = '';
            localidadSelect.innerHTML = '';
            data.forEach(item => crearOpcion(item, municipioSelect));
        }

        if (select === "localidad") {
            localidadSelect.innerHTML = '';
            data.forEach(item => crearOpcion(item, localidadSelect));
        }
    } catch (error) {
        console.error('Error al cargar opciones:', error);
    }
}

function crearOpcion({ id, nombre, nombre_region }, select) {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = nombre || nombre_region;
    select.appendChild(option);
}

document.addEventListener('DOMContentLoaded', function() {
    // Array para almacenar todos los archivos seleccionados
    let selectedFiles = [];
    
    const imageInput = document.getElementById('imagenesInput');
    const addImagesBtn = document.getElementById('addImagesBtn');
    const imageCount = document.getElementById('imageCount');
    const selectedImagesInfo = document.getElementById('selectedImagesInfo');
    
    if (imageInput && addImagesBtn) {
        // Botón para abrir selector de archivos
        addImagesBtn.addEventListener('click', function() {
            imageInput.click();
        });
        
        // Manejar selección de archivos
        imageInput.addEventListener('change', function(e) {
            const newFiles = Array.from(e.target.files);
            
            // Agregar nuevos archivos al array existente
            newFiles.forEach(file => {
                // Verificar que no esté duplicado (por nombre y tamaño)
                const isDuplicate = selectedFiles.some(existingFile => 
                    existingFile.name === file.name && existingFile.size === file.size
                );
                
                if (!isDuplicate) {
                    selectedFiles.push(file);
                }
            });
            
            // Actualizar la previsualización
            updateImagePreview();
            
            // Limpiar el input para permitir seleccionar los mismos archivos otra vez
            imageInput.value = '';
        });
    }
    
    function updateImagePreview() {
        const previewContainer = document.getElementById('imagePreviewContainer');
        
        if (!previewContainer) {
            console.error('Preview container not found');
            return;
        }
        
        // Limpiar contenedor
        previewContainer.innerHTML = '';
        
        // Actualizar contador
        if (imageCount) {
            imageCount.textContent = selectedFiles.length;
        }
        
        // Mostrar/ocultar info de archivos seleccionados
        if (selectedImagesInfo) {
            if (selectedFiles.length > 0) {
                selectedImagesInfo.classList.remove('d-none');
            } else {
                selectedImagesInfo.classList.add('d-none');
            }
        }
        
        // Crear previsualizaciones
        selectedFiles.forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'col-md-3 col-sm-4 col-6 mb-3';
                    previewDiv.setAttribute('data-file-index', index);
                    
                    previewDiv.innerHTML = `
                        <div class="card position-relative">
                            <!-- Botón para eliminar -->
                            <button type="button" class="btn btn-danger btn-sm position-absolute" 
                                    style="top: 5px; right: 5px; z-index: 10; width: 30px; height: 30px; padding: 0;"
                                    onclick="removeImage(${index})"
                                    title="Eliminar imagen">
                                <i class="fas fa-times"></i>
                            </button>
                            
                            <img src="${e.target.result}" 
                                 class="card-img-top" 
                                 style="height: 150px; object-fit: cover;" 
                                 alt="Preview">
                            
                            <div class="card-body p-2">
                                <small class="text-muted text-truncate d-block">${file.name}</small>
                                <small class="text-muted">${(file.size / 1024).toFixed(1)} KB</small>
                            </div>
                        </div>
                    `;
                    
                    previewContainer.appendChild(previewDiv);
                };
                
                reader.readAsDataURL(file);
            }
        });
        
        // Actualizar el input file con los archivos seleccionados
        updateFileInput();
    }
    
    // Función global para eliminar imágenes (se llama desde onclick)
    window.removeImage = function(index) {
        selectedFiles.splice(index, 1);
        updateImagePreview();
    };
    
    function updateFileInput() {
        // Crear un nuevo DataTransfer para actualizar el input file
        const dt = new DataTransfer();
        
        selectedFiles.forEach(file => {
            dt.items.add(file);
        });
        
        imageInput.files = dt.files;
    }
    
    // ...existing code for foto_legajo...
    const fotoLegajoInput = document.getElementById('id_foto_legajo');
    
    if (fotoLegajoInput) {
        fotoLegajoInput.addEventListener('change', function(e) {
            console.log('foto_legajo change event triggered');
            const file = e.target.files[0];
            const previewContainer = document.getElementById('fotoLegajoPreviewContainer');
            
            if (!previewContainer) {
                console.error('Foto legajo preview container not found');
                return;
            }
            
            previewContainer.innerHTML = '';
            
            if (file && file.type.startsWith('image/')) {
                console.log('Processing foto legajo:', file.name, file.type);
                
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    console.log('Foto legajo loaded successfully');
                    
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'col-md-4 col-sm-6 col-12';
                    
                    previewDiv.innerHTML = `
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Previsualización - Foto Legajo</h5>
                            </div>
                            <img src="${e.target.result}" class="card-img-top" style="height: 200px; object-fit: cover;" alt="Foto Legajo Preview">
                            <div class="card-body p-2">
                                <small class="text-muted text-truncate d-block">${file.name}</small>
                                <small class="text-muted">${(file.size / 1024).toFixed(1)} KB</small>
                            </div>
                        </div>
                    `;
                    
                    previewContainer.appendChild(previewDiv);
                };
                
                reader.onerror = function(e) {
                    console.error('Error reading foto legajo file:', e);
                };
                
                reader.readAsDataURL(file);
            } else if (file) {
                console.log('Foto legajo file is not an image:', file.type);
                previewContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        El archivo seleccionado no es una imagen válida.
                    </div>
                `;
            }
        });
    } else {
        console.error('foto_legajo input element not found');
    }
});