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
        imageInput.addEventListener('change', function(e) {
            console.log('imagenesInput change event triggered');
            const files = e.target.files;
            console.log('Files selected:', files.length);
            const previewContainer = document.getElementById('imagePreviewContainer');
            
            if (!previewContainer) {
                console.error('Preview container not found');
                return;
            }
            
            previewContainer.innerHTML = '';
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
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
                    };
                    
                    reader.readAsDataURL(file);
                } else {
                }
            }
        });
    } else {
        console.error('imagenesInput element not found');
    }

    const fotoLegajoInput = document.getElementById('id_foto_legajo');
    
    if (fotoLegajoInput) {
        fotoLegajoInput.addEventListener('change', function(e) {
            console.log('foto_legajo change event triggered');
            const file = e.target.files[0]; // Solo un archivo para foto_legajo
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