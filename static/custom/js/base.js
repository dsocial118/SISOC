
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

    // Sidebar hover functionality for collapsed menu
    
    $(document).ready(function() {
        const sidebarMenu = $('.app-sidebar');
        
        // Function to hide menu-open ULs when sidebar is collapsed
        function hideMenuOpenULs() {
            if ($('body').hasClass('sidebar-collapse')) {
                $('.sidebar-menu .nav-item.menu-open>ul').css('display', 'none');
            }
        }
        
        // Function to show menu-open ULs on hover
        function showMenuOpenULs() {
            if ($('body').hasClass('sidebar-collapse')) {
                $('.sidebar-menu .nav-item.menu-open>ul').css('display', 'block');
            }
        }
        
        // Initialize: hide menu-open ULs when sidebar is collapsed
        hideMenuOpenULs();
        
        // Watch for body class changes to handle initial state
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    hideMenuOpenULs();
                }
            });
        });
        observer.observe(document.body, { attributes: true });
        
        // Mouseenter event: show menu-open ULs when hovering over sidebar-menu
        sidebarMenu.on('mouseenter', function() {
            showMenuOpenULs();
        });
        
        // Mouseleave event: hide menu-open ULs when leaving sidebar-menu
        sidebarMenu.on('mouseleave', function() {
            hideMenuOpenULs();
        });

        // TODO: Es un hack para escuchar el evento 'open.lte.push-menu', preferentemente
        // encontrar el flow del adminlte que maneja el sidebar y poder hacer esta operación desde ahí.
        const sidebarElement = document.querySelector('[data-lte-toggle="sidebar"]');     
        if (sidebarElement) {
            sidebarElement.addEventListener('open.lte.push-menu', function(event) {       
                $('.sidebar-menu .nav-item.menu-open>ul').css('display', 'block');
            });
        }

    });
    
