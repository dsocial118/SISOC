"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { validateTargets } = require("./dispositivos_deploy_preflight");

const configPath = path.join(__dirname, "..", "dispositivos-deploy-targets.json");
const validTargets = JSON.parse(fs.readFileSync(configPath, "utf8"));

function cloneTargets() {
  return JSON.parse(JSON.stringify(validTargets));
}

test("acepta el contrato de los tres destinos de Dispositivos", () => {
  assert.deepEqual(validateTargets(validTargets), []);
});

test("rechaza reutilizar el checkout monolítico", () => {
  const targets = cloneTargets();
  targets.qa.app_root_variable = "APP_ROOT";

  assert.match(
    validateTargets(targets).join("\n"),
    /qa\.app_root_variable no puede reutilizar APP_ROOT/,
  );
});

test("rechaza destinos con proyecto Compose compartido", () => {
  const targets = cloneTargets();
  targets.homologacion.compose_project = targets.qa.compose_project;

  assert.match(
    validateTargets(targets).join("\n"),
    /compose_project único/,
  );
});

test("rechaza runner, branch y roles que no corresponden al ambiente", () => {
  const targets = cloneTargets();
  targets.production.branch = "development";
  targets.production.runner_labels = ["self-hosted", "sisoc-qa"];
  targets.production.web_service = "django";

  const errors = validateTargets(targets).join("\n");
  assert.match(errors, /production\.branch debe ser main/);
  assert.match(errors, /production\.runner_labels debe declarar el runner dedicado/);
  assert.match(errors, /production\.web_service debe ser dispositivos-web/);
});

test("el workflow sólo ejecuta validación declarativa y deploy_guard la exige", () => {
  const workflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "dispositivos-deploy-preflight.yml"),
    "utf8",
  );
  const testsWorkflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "tests.yml"),
    "utf8",
  );

  assert.match(workflow, /dispositivos_deploy_preflight:/);
  assert.match(workflow, /node --test \.github\/scripts\/dispositivos_deploy_preflight\.test\.js/);
  assert.doesNotMatch(workflow, /self-hosted|environment:|docker compose/i);
  assert.match(testsWorkflow, /"dispositivos_deploy_preflight",/);
});

test("el deploy aislado no reutiliza el Compose local ni se dispara por push", () => {
  const deployCompose = fs.readFileSync(
    path.join(__dirname, "..", "..", "compose.dispositivos.deploy.yml"),
    "utf8",
  );
  const deployWorkflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "dispositivos-deploy.yml"),
    "utf8",
  );
  const deployScript = fs.readFileSync(
    path.join(__dirname, "..", "..", "scripts", "operacion", "deploy_dispositivos.sh"),
    "utf8",
  );

  assert.match(deployCompose, /dispositivos-web:/);
  assert.match(deployCompose, /dispositivos-migrate:/);
  assert.match(deployCompose, /127\.0\.0\.1:\$\{DISPOSITIVOS_WEB_PORT_FORWARD:-8002\}:8000/);
  assert.doesNotMatch(deployCompose, /mysql:|local-dump|\.:\/sisoc\/|volumes:/i);
  assert.match(deployWorkflow, /^on:\s*\n\s+workflow_dispatch:/m);
  assert.doesNotMatch(deployWorkflow, /^\s+(push|pull_request):/m);
  assert.doesNotMatch(deployWorkflow, /deploy_refresh\.sh/);
  assert.match(deployScript, /fetch origin --prune/);
  assert.match(deployScript, /docker compose/);
  assert.match(deployScript, /chmod 600 "\$ROLLBACK_STATE"/);
  assert.ok(
    deployScript.indexOf('printf \'%s\\n\' "$previous_sha" > "$ROLLBACK_STATE"')
      < deployScript.indexOf('start_source "$EXPECTED_REVISION"'),
    "el SHA previo debe persistirse antes de iniciar el runtime nuevo",
  );
  assert.doesNotMatch(deployScript, /deploy_refresh\.sh/);
});
