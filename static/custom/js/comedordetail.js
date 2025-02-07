async function getTerritoriales(comedorId) {
    const data = {
        Action: "Find",
        Properties: { Locale: "es-ES" },
        Rows: [{ ComedorID: comedorId }],
    };

    const headers = {
        "applicationAccessKey": GESTIONAR_API_KEY,
        "Content-Type": "application/json"
    };

    try {
        const response = await fetch(GESTIONAR_API_CREAR_COMEDOR, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Error al sincronizar con GESTIONAR: ${response.statusText}`);
        }

        const responseData = await response.json();

        if (!responseData || !responseData[0]?.ListadoRelevadoresDisponibles) {
            return [];
        }

        const territorialesData = parseStringToJSON(responseData[0].ListadoRelevadoresDisponibles)

        const populateSelect = (selectId, data) => {
            const select = document.getElementById(selectId);
            if (!select) return;
            data.forEach(territorial => {
                const option = document.createElement("option");
                option.value = JSON.stringify(territorial);
                option.textContent = territorial.nombre;
                select.appendChild(option);
            });
        };

        populateSelect("new_territorial_select", territorialesData);
        populateSelect("update_territorial_select", territorialesData);

        return territorialesData;
    } catch (error) {
        console.error(`Error al sincronizar con GESTIONAR: ${error.message}`);
        return [];
    }
}

function parseStringToJSON(input) {
    return input.split(' , ').map(entry => {
        const [gestionar_uid, nombre] = entry.split('/ ');
        return { gestionar_uid, nombre };
    });
}

document.addEventListener("DOMContentLoaded", () => {
    getTerritoriales(comedorId);
});
