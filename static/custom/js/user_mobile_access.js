// Visibility only: secondary selections never change the master checkbox.
(() => {
  const mobile = document.getElementById('id_es_representante_pwa');
  const coordinator = document.getElementById('id_es_coordinador_equipo_tecnico_pwa');
  const territorial = document.getElementById('id_es_territorial_comedor');

  const show = (id, visible) => {
    const element = document.getElementById(id);
    if (element) {
      element.style.display = visible ? '' : 'none';
    }
  };

  const syncMobileVisibility = () => {
    if (!mobile) return; // Subusers are administered from the PWA.
    const enabled = mobile.checked;
    const readOnly = enabled && Boolean(coordinator?.checked);
    show('mobile-coordinator-toggle-wrapper', enabled);
    show('mobile-coordinator-scope-wrapper', readOnly);
    show('mobile-rendicion-permission-wrapper', enabled && !readOnly);
    show('mobile-pwa-permissions-wrapper', enabled && !readOnly);
    show('backoffice-permisos-card', !enabled);
    show('backoffice-config-card', !enabled);
    show('password-field-wrapper', !enabled);
    show('mobile-password-help', enabled);
  };

  const syncTerritorialVisibility = () => {
    show('territorial-comedor-provincias-wrapper', Boolean(territorial?.checked));
  };

  mobile?.addEventListener('change', syncMobileVisibility);
  coordinator?.addEventListener('change', syncMobileVisibility);
  territorial?.addEventListener('change', syncTerritorialVisibility);
  syncMobileVisibility();
  syncTerritorialVisibility();
})();
