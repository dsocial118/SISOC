


function deleteArchivo(id) {
    $.ajax({

        // Función Ajax para eliminar los archivos
        url: deleteUrl,
        data: {
            'id': id,
        },
        dataType: 'json',
        success: function (data) {
            if (data.deleted) {
                $("#archivo-" + id).remove();
                toastr.options = { "positionClass": "toast-bottom-right", }
                toastr[data.tipo_mensaje](data.mensaje);
            }
        },
        error: (err) => {
            toastr.options = { "positionClass": "toast-bottom-right", }
            toastr["Error"](err);
        }
    });
};

$(document).ready(function () {


    // DropzoneJS Demo Code Start
    Dropzone.autoDiscover = false

    // Get the template HTML and remove it from the doumenthe template HTML and remove it from the doument
    var previewNode = document.querySelector("#template")
    previewNode.id = ""
    var previewTemplate = previewNode.parentNode.innerHTML
    previewNode.parentNode.removeChild(previewNode)

    var myDropzone = new Dropzone(document.body, { // Make the whole body a dropzone
        url: createUrl,
        thumbnailWidth: 60,
        thumbnailHeight: 60,
        parallelUploads: 10,
        previewTemplate: previewTemplate,
        autoQueue: false, // Make sure the files aren't queued until manually added
        previewsContainer: "#previews", // Define the container to display the previews
        clickable: ".fileinput-button" // Define the element that should be used as click trigger to select files.
    })

    myDropzone.on("addedfile", function (file) {
        // Hookup the start button
        console.log("File added:", file);
        file.previewElement.querySelector(".start").onclick = function () { myDropzone.enqueueFile(file) }
    })

    // Update the total progress bar
    myDropzone.on("totaluploadprogress", function (progress) {
        document.querySelector("#total-progress .progress-bar").style.width = progress + "%"
    })

    myDropzone.on("sending", function (file, xhr, formData) {
        // Show the total progress bar when upload starts
        console.log("Sending file:", file);
        document.querySelector("#total-progress").style.opacity = "1"
        // And disable the start button
        file.previewElement.querySelector(".start").setAttribute("disabled", "disabled")

        // Include CSRF token in the request data
        formData.append("csrfmiddlewaretoken", csrf);
        formData.append("pk", pk);

    })

    // Hide the total progress bar when nothing's uploading anymore
    myDropzone.on("queuecomplete", function (progress) {
        document.querySelector("#total-progress").style.opacity = "0"
    })

    // Setup the buttons for all transfers
    // The "add files" button doesn't need to be setup because the config
    // `clickable` has already been specified.
    document.querySelector("#actions .start").onclick = function () {
        myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED))
    }
    document.querySelector("#actions .cancel").onclick = function () {
        myDropzone.removeAllFiles(true)
    }
    // DropzoneJS Demo Code End

    myDropzone.on("success", function (file, response) {
        // La carga del archivo fue exitosa
        // `response` contiene la respuesta JSON del servidor con la información del archivo

        // Verificar si la lista de archivos está vacía
        console.log("File upload successful:", response);
        if (response.response_data_list.length === 0) {
            $("#resultado").html("<div class='col-12 text-center'><h6 class='text-muted'>Sin archivos</h6></div>");
        } else {
            // Limpiar el contenido actual del div "resultado" antes de agregar los archivos
            $("#resultado").html("");

            // Recorrer la lista de archivos en response_data_list
            for (var i = 0; i < response.response_data_list.length; i++) {
                var archivo = response.response_data_list[i];
                console.log(archivo)
                var tipoArchivo = archivo.tipo;

                // Construir el HTML para mostrar el archivo en la lista
                var archivoHTML = `
            <ul class="list-unstyled" id="archivo-${archivo.id}">
                <li class="p-2">
                    <a href="${archivo.archivo_url}" class="" target="_blank" title='${archivo.name}'>
                        ${tipoArchivo === "Imagen" ? `
                        <img src="${archivo.archivo_url}" alt="archivo de imagen" class="rounded" style="width: 60px; height: 60px;">
                        ` : `
                        <i class="fas fa-file text-dark" style="width: 60px; height: 60px; font-size: 60px;"></i>
                        `}
                        <span class="users-list-name">${archivo.name}</span>
                    </a>
                    <span class="users-list-date">
                        <button class="btn btn-danger btn-sm" onclick='deleteArchivo("${archivo.id}")' type="button">Eliminar</button>
                    </span>
                </li>
            </ul>
        `;

                // Agregar el archivo a la lista de archivos
                $("#resultado").append(archivoHTML);
            }

            // Mostrar un mensaje de éxito con Toastr (opcional, asegúrate de tener Toastr incluido)
            toastr.options = { "positionClass": "toast-bottom-right" };
            toastr["success"]("Archivos cargados exitosamente");

            // Recargar la página después de 1 segundo para mostrar los nuevos archivos
            setTimeout(function () {
                window.location.reload();
            }, 1000);
        }




    });

    myDropzone.on("error", function (file, response) {
        // La carga del archivo falló
        // `response` contiene la respuesta JSON del servidor con la información del error

        // Mostrar un mensaje de error con Toastr (opcional, asegúrate de tener Toastr incluido)
        toastr.options = { "positionClass": "toast-bottom-right" };
        toastr["error"](response.error);

        // Recargar la página después de 1 segundo para mostrar los nuevos archivos
        
    });


});