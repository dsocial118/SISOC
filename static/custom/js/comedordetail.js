(() => {
    async function getTerritoriales(comedorId) {
        const payload = {
            Action: 'Find',
            Properties: { Locale: 'es-ES' },
            Rows: [{ ComedorID: comedorId }]
        };

        try {
          const res = await fetch(GESTIONAR_API_CREAR_COMEDOR, {
              method: 'POST',
              headers: {
                  applicationAccessKey: GESTIONAR_API_KEY,
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify(payload)
        });
          if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

          const json = await res.json();
          const raw = json?.[0]?.ListadoRelevadoresDisponibles;
          const items = raw ? parseStringToJSON(raw) : [];

          updateTerritoriales(items);
          return items;
      } catch (e) {
          console.error('Error al sincronizar con GESTIONAR:', e);
          updateTerritoriales([]);
          return [];
      }
    }

    function parseStringToJSON(input) {
        return input
            .split(/\s*,\s*/)
            .filter(Boolean)
            .map(entry => {
                const [gestionar_uid, nombre] = entry.split(/\s*\/\s*/);
                return { gestionar_uid, nombre };
            });
    }

    function updateTerritoriales(items) {
        const frag = document.createDocumentFragment();
        items.forEach(({ gestionar_uid, nombre }) => {
            frag.append(new Option(nombre, JSON.stringify({ gestionar_uid, nombre })));
        });
        document.querySelectorAll('#new_territorial_select, #update_territorial_select')
            .forEach(select => {
                select.innerHTML = '';
                select.appendChild(frag.cloneNode(true));
            });
    }

    // Llamada inmediata
    getTerritoriales(comedorId);
})();
