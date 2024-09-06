
$.widget.bridge("uibutton", $.ui.button);

	//control color logout icon
    $("#logout_icon").hover(function () {
        $(this).addClass("text-danger");
        $(this).removeClass("text-success");
    }, function () {
        $(this).addClass("text-success");
        $(this).removeClass("text-danger");
    });


    //control Darkmode como opcion de usuario
    $("#darkmode").on('click', function () {
        var checked = $('body').hasClass('dark-mode');

        if (checked) {
            $('body').removeClass('dark-mode')
            $("#darkmode_icon").removeClass("fas").addClass("far").attr("title", "Cambiar a modo oscuro");
        } else {
            $('body').addClass('dark-mode')
            $("#darkmode_icon").removeClass("far").addClass("fas").attr("title", "Cambiar a modo claro");
        }
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token }}");
            }
        });

        $.ajax({
            url: '/set_dark_mode/',
            type: 'POST',
            data: { 'dark_mode': checked },
            success: function (data) {
                console.log(data);
            }
        });
    });


    function mostrarRespuesta() {
        var selectElement = document.getElementById("id_nombre3");
        var selectedValue = selectElement.value;
        var respuestaDetalle = document.getElementById("respuestaDetalle");
        // Verificar la opción seleccionada y actualizar el detalle
        if (selectedValue === "Vos sola") {
            respuestaDetalle.innerText = "Vos sola";
         } else if (selectedValue === "Vos con tu pareja") {
            respuestaDetalle.innerText = "Vos con tu pareja";
        } else if (selectedValue === "Tu pareja sola") {
            respuestaDetalle.innerText = "Tu pareja sola";
        } else {
            respuestaDetalle.innerText = "";
        }
    }
