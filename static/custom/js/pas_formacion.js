(function (window, document) {
    const container = document.getElementById("pas-formacion-personas");
    if (!container || !("IntersectionObserver" in window)) {
        return;
    }

    const items = document.getElementById("pas-formacion-personas-items");
    const sentinel = document.getElementById("pas-formacion-scroll-sentinel");
    const status = document.getElementById("pas-formacion-scroll-status");
    let nextPage = container.dataset.nextPage;
    let loading = false;

    const observer = new IntersectionObserver(
        async (entries) => {
            if (!entries[0].isIntersecting || !nextPage || loading) {
                return;
            }
            loading = true;
            status.textContent = "Cargando titulares…";
            const params = new URLSearchParams({
                page: nextPage,
                q: container.dataset.query || "",
                estado_formacion: container.dataset.estadoFormacion || "todos",
                persona: container.dataset.personaId || "",
            });
            try {
                const response = await fetch(`${container.dataset.pageUrl}?${params}`, {
                    credentials: "same-origin",
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const payload = await response.json();
                items.insertAdjacentHTML("beforeend", payload.html);
                nextPage = payload.has_next ? String(payload.next_page) : "";
                status.textContent = nextPage
                    ? "Desplazate para cargar más titulares"
                    : "Fin del padrón filtrado";
                if (!nextPage) {
                    observer.disconnect();
                }
            } catch (error) {
                console.error("No se pudieron cargar más titulares PAS:", error);
                status.textContent = "No se pudieron cargar más titulares.";
            } finally {
                loading = false;
            }
        },
        { root: container, rootMargin: "120px 0px", threshold: 0.1 },
    );

    observer.observe(sentinel);
})(window, document);
