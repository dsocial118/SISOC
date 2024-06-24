document.addEventListener("DOMContentLoaded", function() {

    const INCOMPLETO_OPTION = "Incompleto";
    var selects = document.querySelectorAll('select[name="areaCurso"], select[name="areaOficio"]');
    var maxSelections = 3;

    let idIncompletoFormParent = document.querySelector("#div_id_nivelIncompleto").parentNode.parentNode;
    let sinEduFormalParent = document.querySelector("#div_id_sinEduFormal").parentNode.parentNode;
    let areaCursoParent = document.querySelector("#div_id_areaCurso").parentNode.parentNode;
    let maxNivelParent = document.querySelector("#div_id_max_nivel").parentNode.parentNode;
    let estadoNivelParent = document.querySelector("#div_id_estado_nivel").parentNode.parentNode;

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

    function esconderPreguntasForm()
    {
      idIncompletoFormParent.classList.add("hide");
      sinEduFormalParent.classList.add("hide");
    }
    
    function asisteEscuelaChoices(value){
      if(value == "a"){
        maxNivelParent.classList.remove("hide");
        estadoNivelParent.classList.remove("hide");
        idIncompletoFormParent.classList.add("hide");
        sinEduFormalParent.classList.add("hide");
      }
      else if(value == "b"){
        maxNivelParent.classList.remove("hide");
        estadoNivelParent.classList.remove("hide");
        idIncompletoFormParent.classList.remove("hide");
        sinEduFormalParent.classList.add("hide");
      }
      else if(value == "c"){
        maxNivelParent.classList.add("hide");
        estadoNivelParent.classList.add("hide");
        sinEduFormalParent.classList.remove("hide");
        idIncompletoFormParent.classList.add("hide");

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
        idIncompletoFormParent.classList.remove("hide");
        sinEduFormalParent.classList.remove("hide");
      }
      else
      {
        esconderPreguntasForm();
      }
    });
    let realizandoCursoForm = document.querySelector('#id_realizandoCurso');
    if (realizandoCursoForm.value == "False"){
      areaCursoParent.classList.add("hide");
    }
    realizandoCursoForm.addEventListener('change',function(event){
      if ( event.target.value == 'True')
        areaCursoParent.classList.remove("hide"); //classList.remove es para eliminar una clase de un elemento
      else{
        areaCursoParent.classList.add("hide"); //classList.add es para agregar una clase a un elemento
        //la clase hide esconde visualmente a un elemento en el DOM
        //event.taget es el elemento al que aplica el listener.
      }
    });

});
