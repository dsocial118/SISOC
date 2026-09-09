document.addEventListener("DOMContentLoaded", () => {
    const selector = document.getElementById("pas-ddjj-version");
    selector?.addEventListener("change", () => {
        window.location.assign(selector.value);
    });

    if (window.location.hash === "#ddjj-panel") {
        const trigger = document.getElementById("ddjj-tab");
        if (trigger && window.bootstrap?.Tab) {
            window.bootstrap.Tab.getOrCreateInstance(trigger).show();
        }
    }
});
