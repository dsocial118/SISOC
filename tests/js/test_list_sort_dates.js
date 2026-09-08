const assert = require('assert');

global.document = {
  addEventListener() {},
};

const { parseDateForSort } = require('../../static/custom/js/listSort.js');

assert.strictEqual(
  parseDateForSort('04/12/2013'),
  Date.UTC(2013, 11, 4),
);
assert.ok(
  parseDateForSort('04/12/2013') > parseDateForSort('10/01/2012'),
  'El orden debe comparar año, mes y día, no solamente el día visible.',
);
assert.strictEqual(parseDateForSort('sin fecha'), null);

console.log('listSort ordena fechas dd/mm/aaaa cronológicamente');
