"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { classifyChangedPaths, isRelevantPath } = require("./dispositivos_build_gate");

test("clasifica cambios del vertical y sus contratos como relevantes", () => {
  const result = classifyChangedPaths([
    "services/dispositivos/application/contracts/v1/identity.py",
  ]);

  assert.deepEqual(result, {
    relevant: true,
    matchingPaths: ["services/dispositivos/application/contracts/v1/identity.py"],
  });
});

test("clasifica los inputs del build como relevantes", () => {
  for (const filePath of [
    "compose.dispositivos.yml",
    "compose.dispositivos.deploy.yml",
    "config/settings.py",
    "docker/django/Dockerfile",
    "docker/django/entrypoint.py",
    "requirements.txt",
    "requirements/dev.txt",
  ]) {
    assert.equal(isRelevantPath(filePath), true, filePath);
  }
});

test("protege los archivos que definen el pipeline", () => {
  assert.equal(isRelevantPath(".github/workflows/dispositivos-build.yml"), true);
  assert.equal(isRelevantPath(".github/scripts/dispositivos_build_gate.js"), true);
  assert.equal(
    isRelevantPath(".github/workflows/dispositivos-deploy-preflight.yml"),
    true,
  );
  assert.equal(isRelevantPath(".github/workflows/dispositivos-deploy.yml"), true);
  assert.equal(isRelevantPath("scripts/operacion/deploy_dispositivos.sh"), true);
  assert.equal(isRelevantPath(".github/workflows/tests.yml"), true);
  assert.equal(
    isRelevantPath(".github/scripts/dispositivos_build_gate.test.js"),
    true,
  );
  assert.equal(isRelevantPath(".github/dispositivos-deploy-targets.json"), true);
});

test("deja como N/A los cambios ajenos al vertical", () => {
  assert.deepEqual(classifyChangedPaths(["centrodeinfancia/forms.py"]), {
    relevant: false,
    matchingPaths: [],
  });
});

test("una mezcla de cambios conserva sólo los paths relevantes", () => {
  assert.deepEqual(
    classifyChangedPaths([
      "docs/indice.md",
      "services\\dispositivos\\runtime\\settings.py",
      "VAT/views.py",
      ".github/workflows/dispositivos-build.yml",
    ]),
    {
      relevant: true,
      matchingPaths: [
        "services/dispositivos/runtime/settings.py",
        ".github/workflows/dispositivos-build.yml",
      ],
    },
  );
});

test("el workflow publica siempre el gate y deploy_guard lo exige", () => {
  const workflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "dispositivos-build.yml"),
    "utf8",
  );
  const testsWorkflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "tests.yml"),
    "utf8",
  );

  assert.match(
    workflow,
    /classify_changes:\s+runs-on: ubuntu-latest\s+outputs:\s+relevant:/,
  );
  assert.match(
    workflow,
    /build_manifest:\s+needs: classify_changes\s+if: \$\{\{ needs\.classify_changes\.outputs\.relevant == 'true' \}\}/,
  );
  assert.match(
    workflow,
    /dispositivos_build_gate:\s+if: \$\{\{ always\(\) \}\}\s+needs:/,
  );
  assert.match(testsWorkflow, /"dispositivos_build_gate",/);
});
