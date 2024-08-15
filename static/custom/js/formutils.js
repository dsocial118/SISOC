class FormUtils{
    static mostrar(id, mostrar = true) {
        let elemento = document.querySelector(id);
        if (elemento) {
            if (mostrar) {
                elemento.classList.remove("hide");
            } else {
                elemento.classList.add("hide");
            }
        } else {
            console.error(`Elemento no encontrado: ${id}`);
        }
      }
      
      static mostrarOcultar(valor, condiciones) {
        condiciones.forEach(condicion => {
          if (valor == condicion.valor) {
              condicion.mostrar.forEach(id => this.mostrar(id, true));
              condicion.ocultar.forEach(id => this.mostrar(id, false));
          }
      });
      }
      
      static manejarCambioMostrarOcultar(elemento, condiciones) {
        elemento.addEventListener('change', (event) => {
            this.mostrarOcultar(event.target.value, condiciones);
        });
      }
}
