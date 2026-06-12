/**
 * Sistema de cache híbrido para territoriales con indicador de desactualización
 */
(() => {
    const TerritorialCache = {
        isLoading: false,
        lastSync: null,
        territorialOptions: [],
        selectedTerritorial: null,

        elements: {
            newContainer: null,
            newInput: null,
            newHiddenInput: null,
            newSuggestions: null,
            updateSelects: [],
            loadingIndicator: null,
            statusIndicator: null,
            syncButton: null,
            newForm: null
        },

        config: {
            maxRetries: 3,
            retryDelay: 1000,
            staleDataClass: 'territorial-stale',
            loadingClass: 'territorial-loading',
            maxSuggestions: 8
        },

        init() {
            this.initElements();
            this.setupEventListeners();
            this.loadTerritoriales();
        },

        initElements() {
            this.elements.newContainer = document.getElementById('new_territorial_container');
            this.elements.newInput = document.getElementById('new_territorial_input');
            this.elements.newHiddenInput = document.getElementById('new_territorial_value');
            this.elements.newSuggestions = document.getElementById('new_territorial_suggestions');
            this.elements.updateSelects = Array.from(
                document.querySelectorAll('select[id*="update_territorial_select"]')
            );
            this.elements.newForm = this.elements.newInput ? this.elements.newInput.closest('form') : null;

            this.createStatusIndicators();
        },

        createStatusIndicators() {
            if (this.elements.statusIndicator) {
                return;
            }

            const indicator = document.createElement('div');
            indicator.id = 'territorial-status';
            indicator.className = 'territorial-status';
            indicator.innerHTML = `
                <span class="status-text">Cargando territoriales...</span>
                <button class="sync-btn" title="Sincronizar con GESTIONAR">
                    <i class="fas fa-sync-alt"></i>
                </button>
            `;

            const firstControl = this.elements.newContainer || this.elements.newInput || this.elements.updateSelects[0];
            if (firstControl) {
                firstControl.parentNode.insertBefore(indicator, firstControl);
            }

            this.elements.statusIndicator = indicator.querySelector('.status-text');
            this.elements.syncButton = indicator.querySelector('.sync-btn');
        },

        setupEventListeners() {
            if (this.elements.syncButton) {
                this.elements.syncButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.forceSync();
                });
            }

            this.getAllControls().forEach((control) => {
                control.addEventListener('focus', () => {
                    if (this.isDataTooOld()) {
                        this.loadTerritoriales();
                    }
                });
            });

            if (this.elements.newInput) {
                this.elements.newInput.addEventListener('input', () => {
                    this.handleTerritorialSearch();
                });

                this.elements.newInput.addEventListener('focus', () => {
                    this.handleTerritorialSearch();
                });

                this.elements.newInput.addEventListener('keydown', (event) => {
                    if (event.key === 'Escape') {
                        this.hideTerritorialSuggestions();
                    }

                    if (event.key === 'Enter') {
                        const exactTerritorial = this.resolveTerritorialSelection(this.elements.newInput.value);
                        if (exactTerritorial) {
                            event.preventDefault();
                            this.setTerritorialSelection(exactTerritorial);
                        }
                    }
                });
            }

            if (this.elements.newForm) {
                this.elements.newForm.addEventListener('submit', (event) => {
                    const exactTerritorial = this.resolveTerritorialSelection(
                        this.elements.newInput?.value || ''
                    );

                    if (exactTerritorial) {
                        this.setTerritorialSelection(exactTerritorial);
                        return;
                    }

                    if (this.elements.newHiddenInput) {
                        this.elements.newHiddenInput.value = '';
                    }

                    event.preventDefault();
                    this.showErrorMessage('Seleccioná un territorial de la lista antes de crear el relevamiento.');
                    this.elements.newInput?.focus();
                });
            }

            document.addEventListener('click', (event) => {
                if (!this.elements.newSuggestions || !this.elements.newInput) {
                    return;
                }

                if (this.elements.newSuggestions.contains(event.target) || event.target === this.elements.newInput) {
                    return;
                }

                this.hideTerritorialSuggestions();
            });
        },

        getAllControls() {
            return [
                this.elements.newInput,
                ...this.elements.updateSelects
            ].filter(Boolean);
        },

        getAllSelects() {
            return [...this.elements.updateSelects].filter(Boolean);
        },

        normalizeText(value) {
            return (value || '')
                .toString()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLowerCase()
                .trim();
        },

        buildTerritorialPayload(territorial) {
            return JSON.stringify({
                gestionar_uid: territorial.gestionar_uid,
                nombre: territorial.nombre
            });
        },

        normalizeTerritoriales(territoriales) {
            return (territoriales || []).map((territorial) => ({
                ...territorial,
                searchKey: this.normalizeText(territorial.nombre),
                payload: this.buildTerritorialPayload(territorial)
            }));
        },

        resolveTerritorialSelection(query) {
            const searchKey = this.normalizeText(query);
            if (!searchKey) {
                return null;
            }

            return this.territorialOptions.find((territorial) => territorial.searchKey === searchKey) || null;
        },

        filterTerritoriales(query) {
            const searchKey = this.normalizeText(query);
            const matches = searchKey
                ? this.territorialOptions.filter((territorial) => territorial.searchKey.includes(searchKey))
                : this.territorialOptions;

            return matches.slice(0, this.config.maxSuggestions);
        },

        handleTerritorialSearch() {
            if (!this.elements.newInput || !this.elements.newHiddenInput || !this.elements.newSuggestions) {
                return;
            }

            const exactTerritorial = this.resolveTerritorialSelection(this.elements.newInput.value);
            if (exactTerritorial) {
                this.setTerritorialSelection(exactTerritorial);
                return;
            }

            this.selectedTerritorial = null;
            this.elements.newHiddenInput.value = '';

            const matches = this.filterTerritoriales(this.elements.newInput.value);
            this.renderTerritorialSuggestions(matches);
        },

        renderTerritorialSuggestions(matches) {
            if (!this.elements.newSuggestions) {
                return;
            }

            this.elements.newSuggestions.innerHTML = '';

            if (!matches.length) {
                const emptyState = document.createElement('div');
                emptyState.className = 'territorial-suggestion-empty';
                emptyState.textContent = 'No hay territoriales que coincidan';
                this.elements.newSuggestions.appendChild(emptyState);
                this.showTerritorialSuggestions();
                return;
            }

            matches.forEach((territorial) => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'territorial-suggestion-item';
                item.textContent = territorial.nombre;

                if (territorial.desactualizado) {
                    item.classList.add('territorial-suggestion-stale');
                }

                item.addEventListener('mousedown', (event) => {
                    event.preventDefault();
                    this.setTerritorialSelection(territorial);
                });

                this.elements.newSuggestions.appendChild(item);
            });

            this.showTerritorialSuggestions();
        },

        refreshTerritorialSuggestions() {
            if (!this.elements.newInput || !this.elements.newSuggestions) {
                return;
            }

            if (this.elements.newSuggestions.classList.contains('d-none')) {
                return;
            }

            this.handleTerritorialSearch();
        },

        showTerritorialSuggestions() {
            if (this.elements.newSuggestions) {
                this.elements.newSuggestions.classList.remove('d-none');
            }
        },

        hideTerritorialSuggestions() {
            if (this.elements.newSuggestions) {
                this.elements.newSuggestions.classList.add('d-none');
            }
        },

        setTerritorialSelection(territorial) {
            this.selectedTerritorial = territorial;

            if (this.elements.newInput) {
                this.elements.newInput.value = territorial ? territorial.nombre : '';
            }

            if (this.elements.newHiddenInput) {
                this.elements.newHiddenInput.value = territorial ? territorial.payload : '';
            }

            this.hideTerritorialSuggestions();
        },

        updateTerritorialData(territoriales, meta) {
            this.territorialOptions = this.normalizeTerritoriales(territoriales);
            this.updateSelects(territoriales, meta);
            this.refreshTerritorialSuggestions();
        },

        async loadTerritoriales(forceSync = false) {
            if (this.isLoading) return;

            this.isLoading = true;
            this.setLoadingState(true);

            try {
                const url = `/comedores/${comedorId}/territoriales/${forceSync ? '?force_sync=true' : ''}`;

                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cache-Control': forceSync ? 'no-cache' : 'max-age=600'
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.success) {
                    const territoriales = Array.isArray(data.territoriales) ? data.territoriales : [];
                    const meta = data.meta || { total: territoriales.length };
                    this.updateTerritorialData(territoriales, meta);
                    this.updateStatus(meta);
                    this.lastSync = new Date();
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            } catch (error) {
                console.error('Error cargando territoriales:', error);
                this.handleError(error);
            } finally {
                this.isLoading = false;
                this.setLoadingState(false);
            }
        },

        async forceSync() {
            if (this.isLoading) return;

            try {
                this.setLoadingState(true, 'Sincronizando con GESTIONAR...');

                const response = await fetch(`/comedores/${comedorId}/territoriales/sincronizar/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    const territoriales = Array.isArray(data.territoriales) ? data.territoriales : [];
                    const meta = data.meta || { total: territoriales.length };
                    this.updateTerritorialData(territoriales, meta);
                    this.updateStatus(meta);
                    this.showSuccessMessage('Territoriales sincronizados correctamente');
                } else {
                    throw new Error(data.error || 'Error en sincronización');
                }
            } catch (error) {
                console.error('Error en sincronización forzada:', error);
                this.handleError(error);
            } finally {
                this.setLoadingState(false);
            }
        },

        updateSelects(territoriales, meta) {
            const selects = this.getAllSelects();
            const currentMeta = meta || { desactualizados: false };

            selects.forEach((select) => {
                if (!select) return;

                const currentValue = select.value;
                const firstOption = select.options[0];

                select.innerHTML = '';
                if (firstOption) {
                    select.appendChild(firstOption);
                }

                territoriales.forEach((territorial) => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify({
                        gestionar_uid: territorial.gestionar_uid,
                        nombre: territorial.nombre
                    });
                    option.textContent = territorial.nombre;

                    if (territorial.desactualizado || currentMeta.desactualizados) {
                        option.className = this.config.staleDataClass;
                        option.title = 'Datos posiblemente desactualizados';
                    }

                    select.appendChild(option);
                });

                if (currentValue) {
                    select.value = currentValue;
                }

                select.classList.toggle(this.config.staleDataClass, Boolean(currentMeta.desactualizados));
            });
        },

        updateStatus(meta) {
            if (!this.elements.statusIndicator) return;

            const statusMeta = meta || {};
            let statusText = '';
            let statusClass = '';

            switch (statusMeta.fuente) {
                case 'cache_provincia':
                    statusText = `${statusMeta.total} territoriales (desde cache rápido)`;
                    statusClass = 'status-success';
                    break;
                case 'db_provincia':
                    statusText = `${statusMeta.total} territoriales (desde cache local)`;
                    statusClass = statusMeta.desactualizados ? 'status-warning' : 'status-success';
                    break;
                case 'gestionar_provincia_sync':
                    statusText = `${statusMeta.total} territoriales (sincronizado)`;
                    statusClass = 'status-success';
                    break;
                case 'fallback_provincia':
                    statusText = `${statusMeta.total} territoriales (datos antiguos)`;
                    statusClass = 'status-warning';
                    break;
                case 'sin_datos':
                    statusText = `${statusMeta.total} territoriales (sin datos)`;
                    statusClass = 'status-warning';
                    break;
                case 'comedor_no_encontrado':
                    statusText = 'Comedor no encontrado';
                    statusClass = 'status-error';
                    break;
                case 'datos_ejemplo':
                    statusText = `${statusMeta.total} territoriales (datos de desarrollo)`;
                    statusClass = 'status-info';
                    break;
                case 'vacio':
                    statusText = `${Number(statusMeta.total) || 0} territoriales (sin datos)`;
                    statusClass = 'status-warning';
                    break;
                default:
                    statusText = 'Error cargando territoriales';
                    statusClass = 'status-error';
                    break;
            }

            if (statusMeta.desactualizados && statusMeta.fuente !== 'fallback_provincia') {
                statusText += ' (algunos desactualizados)';
                statusClass = 'status-warning';
            }

            this.elements.statusIndicator.textContent = statusText;
            this.elements.statusIndicator.className = `status-text ${statusClass}`;
        },

        setLoadingState(isLoading, customMessage = null) {
            const controls = this.getAllControls();
            const message = customMessage || (isLoading ? 'Cargando...' : 'Territoriales cargados');

            controls.forEach((control) => {
                if (control) {
                    control.disabled = isLoading;
                    control.classList.toggle(this.config.loadingClass, isLoading);
                }
            });

            if (this.elements.newSuggestions && isLoading) {
                this.hideTerritorialSuggestions();
            }

            if (this.elements.syncButton) {
                this.elements.syncButton.disabled = isLoading;
                const icon = this.elements.syncButton.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-spin', isLoading);
                }
            }

            if (this.elements.statusIndicator && isLoading) {
                this.elements.statusIndicator.textContent = message;
                this.elements.statusIndicator.className = 'status-text status-loading';
            }
        },

        handleError(error) {
            console.error('Error en TerritorialCache:', error);

            if (this.elements.statusIndicator) {
                this.elements.statusIndicator.textContent = 'Error: ' + error.message;
                this.elements.statusIndicator.className = 'status-text status-error';
            }

            this.showErrorMessage('Error cargando territoriales: ' + error.message);
        },

        showSuccessMessage(message) {
            this.showToast(message, 'success');
        },

        showErrorMessage(message) {
            this.showToast(message, 'error');
        },

        showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 4px;
                color: white;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s;
            `;

            switch (type) {
                case 'success':
                    toast.style.backgroundColor = '#28a745';
                    break;
                case 'error':
                    toast.style.backgroundColor = '#dc3545';
                    break;
                case 'warning':
                    toast.style.backgroundColor = '#ffc107';
                    toast.style.color = '#000';
                    break;
                default:
                    toast.style.backgroundColor = '#17a2b8';
            }

            document.body.appendChild(toast);
            window.setTimeout(() => {
                toast.style.opacity = '1';
            }, 100);

            window.setTimeout(() => {
                toast.style.opacity = '0';
                window.setTimeout(() => document.body.removeChild(toast), 300);
            }, 5000);
        },

        isDataTooOld() {
            if (!this.lastSync) return true;

            const maxAge = 10 * 60 * 1000;
            return (new Date() - this.lastSync) > maxAge;
        }
    };

    const styles = `
        <style>
        .territorial-status {
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 4px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.875rem;
        }

        .status-text {
            flex: 1;
        }

        .status-success { color: #28a745; }
        .status-warning { color: #856404; background-color: #fff3cd; }
        .status-error { color: #721c24; background-color: #f8d7da; }
        .status-info { color: #0c5460; background-color: #d1ecf1; }
        .status-loading { color: #0c5460; }

        .territorial-autocomplete {
            position: relative;
        }

        .territorial-suggestions {
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            right: 0;
            z-index: 1060;
            max-height: 260px;
            overflow-y: auto;
            border: 1px solid #ced4da;
            border-radius: 0.375rem;
            background: #fff;
            box-shadow: 0 0.75rem 1.5rem rgba(0, 0, 0, 0.12);
        }

        .territorial-suggestion-item,
        .territorial-suggestion-empty {
            width: 100%;
            display: block;
            padding: 0.55rem 0.75rem;
            border: 0;
            background: transparent;
            text-align: left;
            font-size: 0.875rem;
            color: #212529;
        }

        .territorial-suggestion-item:hover,
        .territorial-suggestion-item:focus {
            background: #f8f9fa;
            color: #212529;
            outline: none;
        }

        .territorial-suggestion-stale {
            color: #856404;
        }

        .territorial-suggestion-empty {
            color: #6c757d;
        }

        .sync-btn {
            background: #007bff;
            border: none;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.75rem;
        }

        .sync-btn:hover {
            background: #0056b3;
        }

        .sync-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }

        .territorial-loading {
            opacity: 0.6;
            cursor: wait;
        }
        </style>
    `;

    document.head.insertAdjacentHTML('beforeend', styles);

    document.addEventListener('DOMContentLoaded', () => {
        TerritorialCache.init();
    });
})();
