/**
 * Galería de Imágenes - Funcionalidad para comedor detail
 * Maneja la carga de imágenes, modal de vista ampliada y navegación
 */

// Variables globales para la galería
let imagenesData = [];
let imagenActualIndex = 0;

// Inicializar la galería al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    inicializarGaleria();
    cargarImagenesExistentes();
});

/**
 * Inicializa la galería recopilando datos de las imágenes
 */
function inicializarGaleria() {
    // Recopilar datos de las imágenes
    const imageElements = document.querySelectorAll('.imagen-item');
    imagenesData = Array.from(imageElements).map((element, index) => {
        const container = element.querySelector('.imagen-container');
        const nombreElement = element.querySelector('.imagen-nombre');
        
        return {
            url: container.getAttribute('data-image-url'),
            nombre: nombreElement ? nombreElement.textContent.trim() : `imagen_${index + 1}.jpg`,
            index: index
        };
    });
    
    
}

/**
 * Carga las imágenes existentes con manejo de errores y estados
 */
function cargarImagenesExistentes() {
    const imageContainers = document.querySelectorAll('.imagen-container');
    
    imageContainers.forEach((container, index) => {
        const imageUrl = container.getAttribute('data-image-url');
        const placeholder = container.querySelector('.placeholder-imagen');
        
        if (imageUrl && placeholder) {
            // Agregar clase loading
            placeholder.classList.add('loading');
            
            const img = document.createElement('img');
            img.alt = `Imagen del comedor ${index + 1}`;
            img.src = imageUrl;
            
            img.onload = function() {
                placeholder.replaceWith(img);
            };

            img.onerror = function() {
                console.error(`Error al cargar imagen ${index}: ${imageUrl}`);
                placeholder.classList.remove('loading');
                placeholder.innerHTML = '<i class="fas fa-exclamation-triangle"></i><br><small>Error al cargar</small>';
                placeholder.style.background = '#dc3545';
            };
            
            // Timeout de seguridad
            setTimeout(() => {
                if (placeholder.parentNode === container) {
                    placeholder.classList.remove('loading');
                    placeholder.innerHTML = '<i class="fas fa-clock"></i><br><small>Tiempo agotado</small>';
                    placeholder.style.background = '#ffc107';
                    placeholder.style.color = '#000';
                }
            }, 15000);
        } else {
            if (placeholder) {
                placeholder.innerHTML = '<i class="fas fa-question-circle"></i><br><small>Sin imagen</small>';
                placeholder.style.background = '#6c757d';
            }
        }
    });
}

/**
 * Abre el modal con la imagen seleccionada
 * @param {number} index - Índice de la imagen a mostrar
 */
function abrirModal(index) {
    if (index < 0 || index >= imagenesData.length) {
        console.error('Índice de imagen inválido:', index);
        return;
    }

    imagenActualIndex = index;
    const imagen = imagenesData[index];
    
    // Actualizar contenido del modal
    document.getElementById('imagenPrincipal').src = imagen.url;
    document.getElementById('nombreArchivo').textContent = imagen.nombre;
    document.getElementById('contadorImagenes').textContent = `${index + 1} de ${imagenesData.length}`;
    
    // Actualizar estado de botones de navegación
    const btnAnterior = document.querySelector('.btn-anterior');
    const btnSiguiente = document.querySelector('.btn-siguiente');
    
    btnAnterior.disabled = (index === 0);
    btnSiguiente.disabled = (index === imagenesData.length - 1);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('imagenModal'));
    modal.show();
}

/**
 * Cambia a la imagen anterior o siguiente
 * @param {number} direccion - -1 para anterior, 1 para siguiente
 */
function cambiarImagen(direccion) {
    const nuevoIndex = imagenActualIndex + direccion;
    
    if (nuevoIndex >= 0 && nuevoIndex < imagenesData.length) {
        const imagen = imagenesData[nuevoIndex];
        
        // Actualizar imagen con efecto de transición
        const imgElement = document.getElementById('imagenPrincipal');
        imgElement.style.opacity = '0.3';
        
        setTimeout(() => {
            imgElement.src = imagen.url;
            imgElement.style.opacity = '1';

            // Actualizar información
            document.getElementById('nombreArchivo').textContent = imagen.nombre;
            document.getElementById('contadorImagenes').textContent = `${nuevoIndex + 1} de ${imagenesData.length}`;

            // Actualizar botones
            document.querySelector('.btn-anterior').disabled = (nuevoIndex === 0);
            document.querySelector('.btn-siguiente').disabled = (nuevoIndex === imagenesData.length - 1);

            imagenActualIndex = nuevoIndex;
        }, 150);
    }
}

/**
 * Descarga la imagen actual
 */
function descargarImagen() {
    if (imagenActualIndex >= 0 && imagenActualIndex < imagenesData.length) {
        const imagen = imagenesData[imagenActualIndex];
        
        // Crear enlace temporal para descarga
        const link = document.createElement('a');
        link.href = imagen.url;
        link.download = imagen.nombre;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Controles de teclado para el modal
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('imagenModal');
    if (modal && modal.classList.contains('show')) {
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                cambiarImagen(-1);
                break;
            case 'ArrowRight':
                e.preventDefault();
                cambiarImagen(1);
                break;
            case 'Escape':
                e.preventDefault();
                const bootstrapModal = bootstrap.Modal.getInstance(modal);
                if (bootstrapModal) {
                    bootstrapModal.hide();
                }
                break;
        }
    }
});

// Funciones globales accesibles desde el HTML
window.abrirModal = abrirModal;
window.cambiarImagen = cambiarImagen;
window.descargarImagen = descargarImagen;
