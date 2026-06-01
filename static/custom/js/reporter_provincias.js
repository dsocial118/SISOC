document.addEventListener("DOMContentLoaded", () => {
    const filterForm = document.getElementById("reporterFiltersForm");
    const quickSearch = document.getElementById("reporterQuickSearch");
    const quickCounter = document.getElementById("reporterQuickCounter");
    const tableRows = Array.from(document.querySelectorAll("[data-reporter-row]"));

    const submitFilterForm = () => {
        if (!filterForm) {
            return;
        }

        const disabledFields = [];

        Array.from(filterForm.elements).forEach((field) => {
            if (!field.name || field.disabled || ["submit", "button"].includes(field.type)) {
                return;
            }

            if (!String(field.value ?? "").trim()) {
                field.disabled = true;
                disabledFields.push(field);
            }
        });

        filterForm.requestSubmit();

        setTimeout(() => {
            disabledFields.forEach((field) => {
                field.disabled = false;
            });
        }, 0);
    };

    if (filterForm) {
        const filterButtons = document.querySelectorAll("[data-filter-param]");

        filterForm.addEventListener("submit", () => {
            Array.from(filterForm.elements).forEach((field) => {
                if (
                    field.name
                    && !field.disabled
                    && !["submit", "button"].includes(field.type)
                    && !String(field.value ?? "").trim()
                ) {
                    field.disabled = true;
                }
            });
        });

        filterButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const param = button.dataset.filterParam;
                const value = button.dataset.filterValue ?? "";
                const targetField = filterForm.querySelector(`[name="${param}"]`);

                if (!targetField) {
                    return;
                }

                targetField.value = value;
                submitFilterForm();
            });
        });
    }

    if (!quickSearch || !quickCounter || !tableRows.length) {
        return;
    }

    const updateTableFilter = () => {
        const term = quickSearch.value.trim().toLowerCase();
        let visibleCount = 0;

        tableRows.forEach((row) => {
            const matches = row.textContent.toLowerCase().includes(term);
            row.hidden = !matches;
            if (matches) {
                visibleCount += 1;
            }
        });

        quickCounter.textContent = `${visibleCount} registros visibles en esta pagina`;
    };

    quickSearch.addEventListener("input", updateTableFilter);
    updateTableFilter();
});