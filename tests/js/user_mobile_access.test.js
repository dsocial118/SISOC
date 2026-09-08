// Run with: node --test tests/js/user_mobile_access.test.js
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { test } = require('node:test');
const { runInNewContext } = require('node:vm');

const root = resolve(__dirname, '../..');
const template = readFileSync(resolve(root, 'users/templates/user/user_form.html'), 'utf8');
const secondaryNames = [...new Set(
  [...template.matchAll(/form\.((?:puede_|es_)\w+)/g)].map(match => match[1]),
)].filter(name => name !== 'es_representante_pwa');

class Element extends EventTarget {
  constructor() {
    super();
    this.checked = false;
    this.style = {};
    this.options = [];
    this.selectedOptions = [];
    this.value = '';
    this.dataset = {};
  }
  querySelectorAll() { return []; }
}

function loadForm(initial = {}) {
  const elements = {};
  for (const match of template.matchAll(/id="([\w-]+)"/g)) {
    elements[match[1]] = new Element();
  }
  for (const match of template.matchAll(/form\.(\w+)/g)) {
    elements[`id_${match[1]}`] = new Element();
  }
  for (const [name, checked] of Object.entries(initial)) {
    elements[`id_${name}`].checked = checked;
  }
  const context = {
    document: { getElementById: id => elements[id] || null },
    window: {}, Event, HTMLInputElement: Element, HTMLButtonElement: Element,
  };
  for (const match of template.matchAll(/<script nonce="[^\"]*">([\s\S]*?)<\/script>/g)) {
    runInNewContext(match[1], context);
  }
  assert.match(template, /static 'custom\/js\/user_mobile_access.js'/);
  runInNewContext(
    readFileSync(resolve(root, 'static/custom/js/user_mobile_access.js'), 'utf8'),
    context,
  );
  const change = (name, checked) => {
    const element = elements[`id_${name}`];
    element.checked = checked;
    element.dispatchEvent(new Event('change', { bubbles: true }));
  };
  return { elements, change };
}

for (const name of secondaryNames) {
  for (const enabled of [false, true]) {
    test(`${name} never changes mobile=${enabled}`, () => {
      const { elements, change } = loadForm({ es_representante_pwa: enabled });
      for (const checked of [true, false, true]) {
        change(name, checked);
        assert.equal(elements.id_es_representante_pwa.checked, enabled);
      }
    });
  }
}

test('hide and restore selections without unchecking them', () => {
  const { elements, change } = loadForm({ es_representante_pwa: true });
  for (const name of secondaryNames) change(name, true);
  change('es_representante_pwa', false);
  for (const name of secondaryNames) assert.equal(elements[`id_${name}`].checked, true);
  for (const id of [
    'mobile-coordinator-toggle-wrapper', 'mobile-coordinator-scope-wrapper',
    'mobile-rendicion-permission-wrapper', 'mobile-pwa-permissions-wrapper',
    'mobile-association-choice-wrapper', 'mobile-organizaciones-wrapper',
    'mobile-comedores-wrapper',
  ]) assert.equal(elements[id].style.display, 'none', id);
  change('es_representante_pwa', true);
  assert.equal(elements.id_es_coordinador_equipo_tecnico_pwa.checked, true);
  assert.equal(elements['mobile-coordinator-toggle-wrapper'].style.display, '');
  assert.equal(elements['mobile-coordinator-scope-wrapper'].style.display, '');
  assert.equal(elements['backoffice-permisos-card'].style.display, 'none');
  assert.equal(elements['mobile-pwa-permissions-wrapper'].style.display, 'none');
  change('es_coordinador_equipo_tecnico_pwa', false);
  assert.equal(elements['mobile-pwa-permissions-wrapper'].style.display, '');
  assert.equal(elements['mobile-association-choice-wrapper'].style.display, '');
});

test('reopening a suspended coordinator hides retained selections', () => {
  const { elements } = loadForm({
    es_representante_pwa: false, es_coordinador_equipo_tecnico_pwa: true,
    puede_gestionar_rendiciones_mobile: true,
  });
  assert.equal(elements.id_es_representante_pwa.checked, false);
  assert.equal(elements.id_es_coordinador_equipo_tecnico_pwa.checked, true);
  assert.equal(elements['mobile-coordinator-toggle-wrapper'].style.display, 'none');
  assert.equal(elements['mobile-coordinator-scope-wrapper'].style.display, 'none');
  assert.equal(elements['mobile-rendicion-permission-wrapper'].style.display, 'none');
});
