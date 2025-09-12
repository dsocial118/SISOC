/**
 * Sistema de cache híbrido para territoriales con indicador de desactualización
 */
(() => {
    const TerritorialCache = {
        // Estado del cache
        isLoading: false,
        lastSync: null,

        // Elementos DOM
        elements: {
            newSelect: null,
            updateSelects: [],
            loadingIndicator: null,
            statusIndicator: null,
            syncButton: null
        },

        // Configuración
        config: {
            maxRetries: 3,
            retryDelay: 1000,
            staleDataClass: 'territorial-stale',
            loadingClass: 'territorial-loading'
        },

        init() {
            this.initElements();
            this.loadTerritoriales();
            this.setupEventListeners();
        },

        initElements() {
            // Selectores principales
            this.elements.newSelect = document.getElementById('new_territorial_select');
            this.elements.updateSelects = Array.from(
                document.querySelectorAll('select[id*="update_territorial_select"]')
            );

            // Crear indicadores de estado si no existen
            this.createStatusIndicators();
        },

        createStatusIndicators() {
            // Crear indicador de estado
            if (!this.elements.statusIndicator) {
                const indicator = document.createElement('div');
                indicator.id = 'territorial-status';
                indicator.className = 'territorial-status';
                indicator.innerHTML = `
                    <span class="status-text">Cargando territoriales...</span>
                    <button class="sync-btn" title="Sincronizar con GESTIONAR">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                `;

                // Insertar antes del primer select
                const firstSelect = this.elements.newSelect || this.elements.updateSelects[0];
                if (firstSelect) {
                    firstSelect.parentNode.insertBefore(indicator, firstSelect);
                }

                this.elements.statusIndicator = indicator.querySelector('.status-text');
                this.elements.syncButton = indicator.querySelector('.sync-btn');
            }
        },

        setupEventListeners() {
            // Botón de sincronización manual
            if (this.elements.syncButton) {
                this.elements.syncButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.forceSync();
                });
            }

            // Recargar al hacer focus en los selects si los datos están muy desactualizados
            [...this.getAllSelects()].forEach(select => {
                select.addEventListener('focus', () => {
                    if (this.isDataTooOld()) {
                        this.loadTerritoriales();
                    }
                });
            });
        },

        getAllSelects() {
            return [
                this.elements.newSelect,
                ...this.elements.updateSelects
            ].filter(Boolean);
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
                    this.updateSelects(data.territoriales, data.meta);
                    this.updateStatus(data.meta);
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
                    this.updateSelects(data.territoriales, data.meta);
                    this.updateStatus(data.meta);
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

            selects.forEach(select => {
                if (!select) return;

                // Preservar selección actual
                const currentValue = select.value;

                // Limpiar opciones excepto la primera (vacía)
                const firstOption = select.options[0];
                select.innerHTML = '';
                if (firstOption) {
                    select.appendChild(firstOption);
                }

                // Agregar territoriales
                territoriales.forEach(territorial => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify({
                        gestionar_uid: territorial.gestionar_uid,
                        nombre: territorial.nombre
                    });
                    option.textContent = territorial.nombre;

                    // Marcar como desactualizado si es necesario
                    if (territorial.desactualizado || meta.desactualizados) {
                        option.className = this.config.staleDataClass;
                        option.title = 'Datos posiblemente desactualizados';
                    }

                    select.appendChild(option);
                });

                // Restaurar selección si aún existe
                if (currentValue) {
                    select.value = currentValue;
                }

                // Marcar el select con clase de estado
                select.classList.toggle(this.config.staleDataClass, meta.desactualizados);
            });
        },

        updateStatus(meta) {
            if (!this.elements.statusIndicator) return;

            let statusText = '';
            let statusClass = '';

            switch (meta.fuente) {
                case 'cache_provincia':
                    statusText = `${meta.total} territoriales (desde cache rápido)`;
                    statusClass = 'status-success';
                    break;

                case 'db_provincia':
                    statusText = `${meta.total} territoriales (desde cache local)`;
                    statusClass = meta.desactualizados ? 'status-warning' : 'status-success';
                    break;

                case 'gestionar_provincia_sync':
                    statusText = `${meta.total} territoriales (sincronizado)`;
                    statusClass = 'status-success';
                    break;

                case 'fallback_provincia':
                    statusText = `${meta.total} territoriales (datos antiguos)`;
                    statusClass = 'status-warning';
                    break;

                case 'sin_datos':
                    statusText = `${meta.total} territoriales (sin datos)`;
                    statusClass = 'status-warning';
                    break;

                case 'comedor_no_encontrado':
                    statusText = 'Comedor no encontrado';
                    statusClass = 'status-error';
                    break;

                case 'datos_ejemplo':
                    statusText = `${meta.total} territoriales (datos de desarrollo)`;
                    statusClass = 'status-info';
                    break;

                case 'vacio': // compat: antiguo nombre para sin_datos
                    const total = Number(meta.total) || 0;
                    statusText = `${total} territoriales (sin datos)`;
                    statusClass = 'status-warning';
                    break;

                case 'error':

                default:
                    statusText = 'Error cargando territoriales';
                    statusClass = 'status-error';
                    break;
            }

            if (meta.desactualizados && meta.fuente !== 'fallback_provincia') {
                statusText += ' (algunos desactualizados)';
                statusClass = 'status-warning';
            }

            this.elements.statusIndicator.textContent = statusText;
            this.elements.statusIndicator.className = `status-text ${statusClass}`;
        },

        setLoadingState(isLoading, customMessage = null) {
            const selects = this.getAllSelects();
            const message = customMessage || (isLoading ? 'Cargando...' : 'Territoriales cargados');

            selects.forEach(select => {
                if (select) {
                    select.disabled = isLoading;
                    select.classList.toggle(this.config.loadingClass, isLoading);
                }
            });

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
            // Implementación básica de toast
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

            // Colores según tipo
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

            // Animar entrada
            setTimeout(() => toast.style.opacity = '1', 100);

            // Auto-remover
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => document.body.removeChild(toast), 300);
            }, 5000);
        },

        isDataTooOld() {
            if (!this.lastSync) return true;

            const maxAge = 10 * 60 * 1000; // 10 minutos
            return (new Date() - this.lastSync) > maxAge;
        }
    };

    // CSS para los estilos
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
        
        .territorial-stale option {
            background-color: #fff3cd;
            color: #856404;
        }
        
        select.territorial-stale {
            border-color: #ffc107;
            background-color: #fff3cd;
        }
        </style>
    `;

    // Inyectar estilos
    document.head.insertAdjacentHTML('beforeend', styles);

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => TerritorialCache.init());
    } else {
        TerritorialCache.init();
    }

    // Exponer globalmente para debugging
    window.TerritorialCache = TerritorialCache;

})();
