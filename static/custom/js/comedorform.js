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
    const imageInput = document.getElementById('imagenesInput');
    
    if (imageInput) {
        imageInput.addEventListener('input', function(e) {
            console.log('imagenesInput change event triggered');
            const files = e.target.files;
            console.log('Files selected:', files.length);
            const previewContainer = document.getElementById('imagePreviewContainer');
            
            if (!previewContainer) {
                console.error('Preview container not found');
                return;
            }
            
            // Limpiar previsualizaciones anteriores
            previewContainer.innerHTML = '';
            
            // Procesar cada archivo seleccionado
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                console.log('Processing file:', file.name, file.type);
                
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        console.log('File loaded successfully');
                        // Crear elemento de previsualización
                        const previewDiv = document.createElement('div');
                        previewDiv.className = 'col-md-3 col-sm-4 col-6 mb-3';
                        
                        previewDiv.innerHTML = `
                            <div class="card">
                                <img src="${e.target.result}" class="card-img-top" style="height: 150px; object-fit: cover;" alt="Preview">
                                <div class="card-body p-2">
                                    <small class="text-muted text-truncate d-block">${file.name}</small>
                                    <small class="text-muted">${(file.size / 1024).toFixed(1)} KB</small>
                                </div>
                            </div>
                        `;
                        
                        previewContainer.appendChild(previewDiv);
                    };
                    
                    reader.onerror = function(e) {
                        console.error('Error reading file:', e);
                    };
                    
                    reader.readAsDataURL(file);
                } else {
                    console.log('File is not an image:', file.type);
                }
            }
        });
    } else {
        console.error('imagenesInput element not found');
    }
});