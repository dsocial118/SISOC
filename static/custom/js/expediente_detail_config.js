// Configuración de URLs para expediente detail
window.PROCESS_URL = document.querySelector('meta[name="process-url"]')?.content;
window.CONFIRM_URL = document.querySelector('meta[name="confirm-url"]')?.content;
window.CRUCE_URL = document.querySelector('meta[name="cruce-url"]')?.content;
window.CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content;
window.REVISAR_URL_TEMPLATE = document.querySelector('meta[name="revisar-url-template"]')?.content;
window.CONFIRM_SUBS_URL = document.querySelector('meta[name="confirm-subs-url"]')?.content;
window.VALIDAR_RENAPER_URL_TEMPLATE = document.querySelector('meta[name="validar-renaper-url-template"]')?.content;