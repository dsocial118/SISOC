"use strict";

const fs = require("node:fs");

const EXPECTED_TARGETS = {
  qa: {
    branch: "development",
    environment: "qa",
    runnerLabel: "sisoc-qa",
  },
  homologacion: {
    branch: "homologacion",
    environment: "homologacion",
    runnerLabel: "sisoc-homologacion",
  },
  production: {
    branch: "main",
    environment: "production",
    runnerLabel: "sisoc-produccion",
  },
};

const REQUIRED_FIELDS = [
  "branch",
  "environment",
  "runner_labels",
  "app_root_variable",
  "env_file_variable",
  "rollback_state_variable",
  "compose_file",
  "compose_project",
  "web_service",
  "migrate_service",
];

const VARIABLE_NAME = /^[A-Z][A-Z0-9_]+$/;

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function validateVariable(value, field, targetName, errors) {
  if (typeof value !== "string" || !VARIABLE_NAME.test(value)) {
    errors.push(`${targetName}.${field} debe ser un nombre de variable válido.`);
  }
}

function validateTarget(targetName, target, errors) {
  const expected = EXPECTED_TARGETS[targetName];
  if (!isObject(target)) {
    errors.push(`${targetName} debe ser un objeto.`);
    return;
  }

  for (const field of REQUIRED_FIELDS) {
    if (!(field in target)) {
      errors.push(`${targetName}.${field} es obligatorio.`);
    }
  }

  if (target.branch !== expected.branch) {
    errors.push(`${targetName}.branch debe ser ${expected.branch}.`);
  }
  if (target.environment !== expected.environment) {
    errors.push(`${targetName}.environment debe ser ${expected.environment}.`);
  }
  if (
    !Array.isArray(target.runner_labels)
    || target.runner_labels.length !== 2
    || target.runner_labels[0] !== "self-hosted"
    || target.runner_labels[1] !== expected.runnerLabel
  ) {
    errors.push(`${targetName}.runner_labels debe declarar el runner dedicado.`);
  }

  for (const field of [
    "app_root_variable",
    "env_file_variable",
    "rollback_state_variable",
  ]) {
    validateVariable(target[field], field, targetName, errors);
  }
  if (target.app_root_variable === "APP_ROOT") {
    errors.push(`${targetName}.app_root_variable no puede reutilizar APP_ROOT.`);
  }

  const variables = [
    target.app_root_variable,
    target.env_file_variable,
    target.rollback_state_variable,
  ];
  if (new Set(variables).size !== variables.length) {
    errors.push(`${targetName} debe usar variables separadas para root, entorno y rollback.`);
  }

  if (target.compose_file !== "compose.dispositivos.yml") {
    errors.push(`${targetName}.compose_file debe usar compose.dispositivos.yml.`);
  }
  if (
    typeof target.compose_project !== "string"
    || !target.compose_project.startsWith("sisoc-dispositivos-")
  ) {
    errors.push(`${targetName}.compose_project debe aislar el proyecto Docker.`);
  }
  if (target.web_service !== "dispositivos-web") {
    errors.push(`${targetName}.web_service debe ser dispositivos-web.`);
  }
  if (target.migrate_service !== "dispositivos-migrate") {
    errors.push(`${targetName}.migrate_service debe ser dispositivos-migrate.`);
  }
}

function validateTargets(targets) {
  const errors = [];
  if (!isObject(targets)) {
    return ["La configuración debe ser un objeto de destinos."];
  }

  const expectedNames = Object.keys(EXPECTED_TARGETS);
  const actualNames = Object.keys(targets);
  for (const targetName of expectedNames) {
    if (!(targetName in targets)) {
      errors.push(`Falta el destino ${targetName}.`);
      continue;
    }
    validateTarget(targetName, targets[targetName], errors);
  }
  for (const targetName of actualNames) {
    if (!(targetName in EXPECTED_TARGETS)) {
      errors.push(`Destino no permitido: ${targetName}.`);
    }
  }

  const projects = expectedNames
    .map((targetName) => targets[targetName]?.compose_project)
    .filter(Boolean);
  if (new Set(projects).size !== projects.length) {
    errors.push("Cada destino debe tener un compose_project único.");
  }

  return errors;
}

function main() {
  const configPath = process.argv[2] || ".github/dispositivos-deploy-targets.json";
  const targets = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const errors = validateTargets(targets);
  if (errors.length > 0) {
    process.stderr.write(`${errors.join("\n")}\n`);
    process.exitCode = 1;
    return;
  }
  process.stdout.write("Preflight declarativo de Dispositivos OK.\n");
}

if (require.main === module) {
  main();
}

module.exports = { EXPECTED_TARGETS, validateTargets };
