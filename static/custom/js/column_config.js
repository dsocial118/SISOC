(function () {
    if (window.__columnConfigInitialized) {
        return;
    }
    window.__columnConfigInitialized = true;
    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    async function readJson(response) {
        const text = await response.text();
        if (!text) {
            return null;
        }
        try {
            return JSON.parse(text);
        } catch (error) {
            return null;
        }
    }

    function showError(modal, message) {
        const errorNode = modal.querySelector('.column-config-error');
        if (!errorNode) {
            return;
        }
        errorNode.textContent = message;
        errorNode.classList.remove('d-none');
    }

    function clearError(modal) {
        const errorNode = modal.querySelector('.column-config-error');
        if (!errorNode) {
            return;
        }
        errorNode.textContent = '';
        errorNode.classList.add('d-none');
    }

    function moveItem(list, item, direction) {
        if (!list || !item) {
            return;
        }
        if (direction === 'up') {
            const prev = item.previousElementSibling;
            if (prev) {
                list.insertBefore(item, prev);
            }
            return;
        }
        if (direction === 'down') {
            const next = item.nextElementSibling;
            if (next) {
                list.insertBefore(item, next.nextElementSibling);
            }
        }
    }

    function getActiveKeys(list) {
        const items = list ? list.querySelectorAll('[data-column-key]') : [];
        const keys = [];
        items.forEach((item) => {
            const checkbox = item.querySelector('.column-config-checkbox');
            if (checkbox && checkbox.checked) {
                keys.push(item.getAttribute('data-column-key'));
            }
        });
        return keys;
    }

    async function saveConfig(modal, config) {
        const list = modal.querySelector('.column-config-list');
        if (!list) {
            return;
        }
        clearError(modal);
        const keys = getActiveKeys(list);
        if (!keys.length) {
            showError(modal, 'Debe haber al menos una columna visible.');
            return;
        }

        try {
            const response = await fetch(config.endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    list_key: config.list_key,
                    columns: keys,
                }),
            });
            const data = await readJson(response);
            if (!response.ok) {
                const message = data && data.error ? data.error : 'No se pudo guardar la configuracion.';
                throw new Error(message);
            }
            window.location.reload();
        } catch (error) {
            showError(modal, error.message || 'No se pudo guardar la configuracion.');
        }
    }

    async function resetConfig(modal, config) {
        clearError(modal);
        try {
            const response = await fetch(config.endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    list_key: config.list_key,
                    reset: true,
                }),
            });
            const data = await readJson(response);
            if (!response.ok) {
                const message = data && data.error ? data.error : 'No se pudo restablecer la configuracion.';
                throw new Error(message);
            }
            window.location.reload();
        } catch (error) {
            showError(modal, error.message || 'No se pudo restablecer la configuracion.');
        }
    }

    function initModal(modal) {
        const configId = modal.dataset.configId;
        if (!configId) {
            return;
        }
        const script = document.getElementById(configId);
        if (!script) {
            return;
        }
        let config;
        try {
            config = JSON.parse(script.textContent);
        } catch (error) {
            return;
        }
        if (!config || !config.endpoint || !config.list_key) {
            return;
        }

        modal.addEventListener('click', (event) => {
            const upButton = event.target.closest('.column-move-up');
            if (upButton) {
                const item = upButton.closest('[data-column-key]');
                const list = modal.querySelector('.column-config-list');
                moveItem(list, item, 'up');
                return;
            }
            const downButton = event.target.closest('.column-move-down');
            if (downButton) {
                const item = downButton.closest('[data-column-key]');
                const list = modal.querySelector('.column-config-list');
                moveItem(list, item, 'down');
                return;
            }
            const saveButton = event.target.closest('.column-config-save');
            if (saveButton) {
                saveConfig(modal, config);
                return;
            }
            const resetButton = event.target.closest('.column-config-reset');
            if (resetButton) {
                resetConfig(modal, config);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const modals = document.querySelectorAll('[data-column-config]');
        modals.forEach(initModal);
    });
})();
