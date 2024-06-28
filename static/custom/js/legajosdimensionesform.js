document.addEventListener("DOMContentLoaded", function() {

    const INCOMPLETO_OPTION = "Incompleto";
    var selects = document.querySelectorAll('select[name="areaCurso"], select[name="areaOficio"]');
    var maxSelections = 3;
    //Variables dimensión Educación

    const ID_INCOMPLETO_FORM ="#container_incompleto";
    const ID_SIN_EDU_FORMAL = "#container_sin_edu";
    const ID_AREA_CURSO = "#container_area_curso";
    const ID_MAX_NIVEL = "#container_max_nivel";
    const ID_ESTADO_NIVEL = "#container_nivel";
    const ID_DATOS_INSTITUCION = "#container_institucion";
    // Fin var educación

    selects.forEach(function(select) {
        select.setAttribute('multiple', 'multiple');

        select.addEventListener('change', function() {
            var selectedOptions = Array.from(select.selectedOptions);
            if (selectedOptions.length > maxSelections) {
                alert('Solo puedes seleccionar hasta 3 opciones.');
                selectedOptions[selectedOptions.length - 1].selected = false;
            }
        });
    });

    let estadoNivelForm = document.querySelector('#id_estado_nivel');
    let asisteEscuelaForm = document.querySelector('#id_asiste_escuela');

    function mostrar (id, mostrar = true){
      elemento = document.querySelector(id)
      if (mostrar == true){
        elemento.classList.remove("hide")
      }
      else {
        elemento.classList.add("hide")
      }
    }


    function esconderPreguntasForm()
    {
      mostrar(ID_INCOMPLETO_FORM, false);
      mostrar(ID_SIN_EDU_FORMAL, false);
    }
    
    function asisteEscuelaChoices(value){
      if(value == "a"){
        mostrar(ID_MAX_NIVEL);
        mostrar(ID_ESTADO_NIVEL);
        mostrar(ID_INCOMPLETO_FORM, false);
        mostrar(ID_SIN_EDU_FORMAL, false);
        mostrar(ID_DATOS_INSTITUCION);
      }
      else if(value == "b"){
        mostrar(ID_MAX_NIVEL);
        mostrar(ID_ESTADO_NIVEL);
        mostrar(ID_INCOMPLETO_FORM);
        mostrar(ID_SIN_EDU_FORMAL, false);
        mostrar(ID_DATOS_INSTITUCION);
      }
      else if(value == "c"){
        mostrar(ID_MAX_NIVEL, false);
        mostrar(ID_ESTADO_NIVEL, false);
        mostrar(ID_SIN_EDU_FORMAL);
        mostrar(ID_INCOMPLETO_FORM, false);
        mostrar(ID_DATOS_INSTITUCION, false);

      }
    }

    asisteEscuelaChoices(asisteEscuelaForm.value);

    //Evento para el cambio en asisteEscuelaForm
    asisteEscuelaForm.addEventListener('change', function(event){
      console.log('Valor seleccionado en asisteEscuelaForm:', event.target.value);
      asisteEscuelaChoices(event.target.value);
    });

    if(estadoNivelForm.value != INCOMPLETO_OPTION)
    {
      esconderPreguntasForm();
    }

    estadoNivelForm.addEventListener('change', function(event) {
      if (event.target.value == INCOMPLETO_OPTION)
      {
        mostrar(ID_INCOMPLETO_FORM);
        mostrar(ID_SIN_EDU_FORMAL);
      }
      else
      {
        esconderPreguntasForm();
      }
    });
    let realizandoCursoForm = document.querySelector('#id_realizandoCurso');
    if (realizandoCursoForm.value == "False"){
      mostrar(ID_AREA_CURSO, false);
    }
    realizandoCursoForm.addEventListener('change',function(event){
      if ( event.target.value == 'True')
        mostrar(ID_AREA_CURSO); //classList.remove es para eliminar una clase de un elemento
      else{
        mostrar(ID_AREA_CURSO, false); //classList.add es para agregar una clase a un elemento
        //la clase hide esconde visualmente a un elemento en el DOM
        //event.taget es el elemento al que aplica el listener.
      }
    });

    //dimension vivienda
    //id="div_id_hay_banio" id_hay_banio si contesta c ("No tiene inodoro") saltea la pregunta 17) id="div_id_desague" id_desague

    let hayBanioForm = document.querySelector("#div_id_hay_banio");
    const ID_DESAGUE_BANIO = "#container_desague";

    hayBanioForm.addEventListener('change',function(event){
      if ( event.target.value == 'No tiene inodoro' || event.target.value == 'No tiene baño')
        mostrar(ID_DESAGUE_BANIO, false); 
      else{
        mostrar(ID_DESAGUE_BANIO);
      }
    });

    //dimension trabajo

    let tieneTrabajoForm = document.querySelector("#div_id_tiene_trabajo");
    let busquedaLaboralForm = document.querySelector("#id_busquedaLaboral");
    const ID_CONVIVIENTE = "#container_conviviente";
    const ID_HS_SEMANALES ="#container_horas_semanales";
    const ID_ACT_REALIZADA_COMO = "#container_actividad_realizada";
    const ID_DURACION_TRABAJO = "#container_duracion_trabajo";
    const ID_APORTE_JUBILACION = "#container_jubilacion";
    const ID_MODO_CONTRATACION = "#container_contratacion";
    const ID_BUSQUEDA_LABORAL = "#container_busquedaLaboral";
    const ID_TIEMPO_BUSQUEDA = "#container_tiempo_busqueda";
    const ID_NO_BUSQUEDA = "#container_no_busqueda";
    const ID_OCUPACION = "#container_ocupacion";

    tieneTrabajoForm.addEventListener('change',function(event){
      if ( event.target.value == "True"){
        mostrar(ID_HS_SEMANALES);
        mostrar(ID_ACT_REALIZADA_COMO);
        mostrar(ID_DURACION_TRABAJO);
        mostrar(ID_APORTE_JUBILACION);
        mostrar(ID_MODO_CONTRATACION);
        mostrar(ID_NO_BUSQUEDA, false);
        mostrar(ID_TIEMPO_BUSQUEDA, false);
        mostrar(ID_BUSQUEDA_LABORAL, false);
      }
      else{
        mostrar(ID_HS_SEMANALES, false); 
        mostrar(ID_ACT_REALIZADA_COMO, false);
        mostrar(ID_DURACION_TRABAJO, false);
        mostrar(ID_APORTE_JUBILACION, false);
        mostrar(ID_MODO_CONTRATACION, false);
        mostrar(ID_BUSQUEDA_LABORAL);
        mostrar(ID_NO_BUSQUEDA, false);
        mostrar(ID_TIEMPO_BUSQUEDA, false);
        

        
      }
    });

    busquedaLaboralForm.addEventListener('change',function(event){
      if ( event.target.value == "True"){
        mostrar(ID_TIEMPO_BUSQUEDA);
        mostrar(ID_NO_BUSQUEDA, false);
        mostrar(ID_OCUPACION);
      }
      else{
        mostrar(ID_NO_BUSQUEDA);
        mostrar(ID_TIEMPO_BUSQUEDA, false);
        mostrar(ID_OCUPACION, false);
        
      }
    });
});

