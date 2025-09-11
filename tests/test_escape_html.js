const assert = require('assert');
// Stub minimal document to satisfy celiaquia_list.js when required in Node
global.document = { addEventListener: () => {} };
const { escapeHtml } = require('../static/custom/js/celiaquia_list.js');

const raw = '<strong>hi</strong> & `test`';
const expected = '&lt;strong&gt;hi&lt;/strong&gt; &amp; &#96;test&#96;';
assert.strictEqual(escapeHtml(raw), expected);
console.log('escapeHtml escapes HTML tags correctly');
