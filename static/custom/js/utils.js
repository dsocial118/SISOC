/* Shared utility helpers */
/**
 * escapeHtml converts a string to its HTML-escaped representation.
 * This prevents browsers from interpreting user-controlled content
 * as markup, mitigating XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Expose helper to browser globals and Node tests
if (typeof window !== 'undefined') {
  window.escapeHtml = escapeHtml;
}
if (typeof module !== 'undefined') {
  module.exports = { escapeHtml };
}
