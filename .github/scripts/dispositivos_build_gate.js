"use strict";

const RELEVANT_PREFIXES = [
  "services/dispositivos/",
  "requirements/",
];

const RELEVANT_PATHS = new Set([
  "compose.dispositivos.yml",
  "config/settings.py",
  "docker/django/Dockerfile",
  "docker/django/entrypoint.py",
  "requirements.txt",
  ".github/workflows/dispositivos-build.yml",
  ".github/workflows/dispositivos-deploy-preflight.yml",
  ".github/workflows/tests.yml",
  ".github/scripts/dispositivos_build_gate.js",
  ".github/scripts/dispositivos_build_gate.test.js",
  ".github/scripts/dispositivos_deploy_preflight.js",
  ".github/scripts/dispositivos_deploy_preflight.test.js",
  ".github/dispositivos-deploy-targets.json",
]);

function normalizePath(filePath) {
  return String(filePath || "").trim().replaceAll("\\", "/");
}

function isRelevantPath(filePath) {
  const normalized = normalizePath(filePath);
  return RELEVANT_PATHS.has(normalized)
    || RELEVANT_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

function classifyChangedPaths(paths) {
  const matchingPaths = paths
    .map(normalizePath)
    .filter(Boolean)
    .filter(isRelevantPath);

  return {
    relevant: matchingPaths.length > 0,
    matchingPaths,
  };
}

function main() {
  const input = require("node:fs").readFileSync(0, "utf8");
  const result = classifyChangedPaths(input.split(/\r?\n/));
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (require.main === module) {
  main();
}

module.exports = {
  RELEVANT_PATHS,
  RELEVANT_PREFIXES,
  classifyChangedPaths,
  isRelevantPath,
};
