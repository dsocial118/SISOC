(() => {
    async function getTerritoriales(comedorId) {
        try {
            const res = await fetch(`/comedores/${comedorId}/territoriales/?force_sync=true`);
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

            const json = await res.json();
            const items = Array.isArray(json?.territoriales) ? json.territoriales : [];

            updateTerritoriales(items);
            return items;
        } catch (e) {
            console.error('Error al sincronizar con GESTIONAR:', e);
            updateTerritoriales([]);
            return [];
        }
    }

    function updateTerritoriales(items) {
        const newOptions = items.map(({ gestionar_uid, nombre }) => {
            const option = new Option(nombre, JSON.stringify({ gestionar_uid, nombre }));
            option.dataset.gestionar = 'true'; // Opcional: para distinguir los nuevos
            return option;
        });

        document.querySelectorAll('#new_territorial_select, #update_territorial_select')
            .forEach(select => {
                newOptions.forEach(option => {
                    select.appendChild(option.cloneNode(true));
                });
            });
    }

    // Llamada inmediata
    getTerritoriales(comedorId);
})();
