// Manual test for escapeHtml utility in cupo_provincia.js
// Run with: node tests/escape_html.test.js
const escapeHtml = (str) =>
  String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));

const unsafe = '<script>alert("xss")</script>';
const safe = escapeHtml(unsafe);
console.log('Escaped output:', safe);
