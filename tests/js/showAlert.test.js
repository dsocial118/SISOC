const { escapeHtml } = require('../../static/custom/js/utils.js');

// Minimal DOM stubs
const documentStub = {
  elements: {},
  body: {
    prepend(el) {
      // no-op for test
    },
  },
  getElementById(id) {
    return this.elements[id] || null;
  },
  createElement(tag) {
    const el = {
      tagName: tag,
      innerHTML: '',
      style: {},
      prepend() {},
      querySelector() { return null; },
      set id(value) {
        this._id = value;
        documentStub.elements[value] = this;
      },
      get id() {
        return this._id;
      },
    };
    return el;
  },
  querySelector() {
    return null;
  },
  addEventListener() {},
};

global.document = documentStub;
global.escapeHtml = escapeHtml;

const { showAlert } = require('../../static/custom/js/expediente_detail.js');

// Test that malicious HTML is rendered as text
const payload = '<img src=x onerror=alert(1) />';
showAlert('danger', payload);
const zone = documentStub.getElementById('expediente-alerts');
if (!zone || zone.innerHTML.includes('<img')) {
  throw new Error('HTML was not escaped');
}
if (!zone.innerHTML.includes('&lt;img')) {
  throw new Error('Escaped text missing');
}
console.log('showAlert escaped HTML correctly');
