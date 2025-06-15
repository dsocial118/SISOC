    function filterTable() {
        let input = document.getElementById("comedorFilter");
        let filter = input.value.toLowerCase();
        let table = document.querySelector("table");
        let tr = table.getElementsByTagName("tr");

        for (let i = 1; i < tr.length; i++) { // empieza en 1 para saltar el encabezado
            let td = tr[i].getElementsByTagName("td")[0]; // columna del nombre
            if (td) {
                let txtValue = td.textContent || td.innerText;
                tr[i].style.display = txtValue.toLowerCase().indexOf(filter) > -1 ? "" : "none";
            }
        }
    }

