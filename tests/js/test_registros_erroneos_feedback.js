const assert = require('assert');

global.document = {
  addEventListener: () => {},
};

const {
  buildReprocesarRegistrosFeedback,
} = require('../../static/custom/js/registros_erroneos.js');

const soloExcluidos = buildReprocesarRegistrosFeedback({
  creados: 0,
  errores: 0,
  excluidos: 1,
});

assert.strictEqual(soloExcluidos.kind, 'warning');
assert.match(soloExcluidos.message, /No se crearon legajos nuevos/);
assert.match(soloExcluidos.message, /1 legajo no se creó porque ya existe/);
assert.doesNotMatch(soloExcluidos.message, /Se crearon 0 legajos correctamente/);
assert.strictEqual(soloExcluidos.shouldQueueSuccess, false);

const creadosOk = buildReprocesarRegistrosFeedback({
  creados: 2,
  errores: 0,
  excluidos: 0,
  alerta_resumen: 'Importacion procesada.',
});

assert.strictEqual(creadosOk.kind, 'success');
assert.match(creadosOk.message, /Se crearon 2 legajos correctamente/);
assert.strictEqual(creadosOk.shouldQueueSuccess, true);
