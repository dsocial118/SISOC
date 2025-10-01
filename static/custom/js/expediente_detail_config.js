// Configuración de URLs para expediente detail
window.PROCESS_URL = document.querySelector('meta[name="process-url"]')?.content;
window.CONFIRM_URL = document.querySelector('meta[name="confirm-url"]')?.content;
window.CRUCE_URL = document.querySelector('meta[name="cruce-url"]')?.content;
window.CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content;

const revisarMeta = document.querySelector('meta[name="revisar-url-template"]');
window.REVISAR_URL_TEMPLATE = revisarMeta?.content?.replace('/0/', '/{id}/');
window.CONFIRM_SUBS_URL = document.querySelector('meta[name="confirm-subs-url"]')?.content;
const validarMeta = document.querySelector('meta[name="validar-renaper-url-template"]');
window.VALIDAR_RENAPER_URL_TEMPLATE = validarMeta?.content?.replace('/0/', '/{id}/');
