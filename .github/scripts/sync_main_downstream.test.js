"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { run, synchronizationBranch } = require("./sync_main_downstream");

test("el workflow carga la automatizacion desde development, donde existe el helper", () => {
  const workflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "sync-main-downstream.yml"),
    "utf8",
  );

  assert.match(
    workflow,
    /name: Checkout de la automatizacion versionada\s+uses: actions\/checkout@v6\.0\.2\s+with:\s+ref: development/,
  );
});

test("deploy_guard ejecuta las pruebas de automatizacion de release", () => {
  const testsWorkflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "tests.yml"),
    "utf8",
  );

  assert.match(
    testsWorkflow,
    /name: Ejecutar pruebas de automatizacion de release\s+run: node --test \.github\/scripts\/release_orchestrator\.test\.js \.github\/scripts\/sync_main_downstream\.test\.js/,
  );
});

test("deploy_guard se ejecuta aunque falle un check requerido", () => {
  const testsWorkflow = fs.readFileSync(
    path.join(__dirname, "..", "workflows", "tests.yml"),
    "utf8",
  );

  assert.match(
    testsWorkflow,
    /deploy_guard:\s+if: \$\{\{ always\(\) && github\.event_name == 'pull_request' \}\}/,
  );
});

test("solo acepta el 204 sin cuerpo para la rama destino ya contenida", async () => {
  const calls = [];
  const errors = [];
  const failures = [];
  let noContentResponse = { status: 204 };
  const github = {
    rest: {
      repos: {
        compareCommits: async ({ head }) => ({
          data: { behind_by: head === "development" ? 1 : 0 },
        }),
        merge: async (payload) => {
          calls.push(["merge", payload]);
          if (payload.head === "development") {
            return noContentResponse;
          }
          return { data: { merged: true } };
        },
      },
      git: {
        getRef: async ({ ref }) => {
          if (ref === "heads/automation/sync-main-to-development") {
            const error = new Error("missing ref");
            error.status = 404;
            throw error;
          }
          return { data: { object: { sha: "development-sha" } } };
        },
        createRef: async (payload) => {
          calls.push(["createRef", payload]);
        },
      },
      pulls: {
        list: async ({ head }) => {
          if (head === "acme:main") {
            return {
              data: [{
                number: 41,
                title: "chore(sync): integrar main en development",
                user: { login: "github-actions[bot]" },
              }],
            };
          }
          return { data: [] };
        },
        update: async (payload) => {
          calls.push(["closeLegacyPull", payload]);
        },
        create: async (payload) => {
          calls.push(["createPull", payload]);
          return { data: { number: 42, html_url: "https://example.test/pr/42", node_id: "pull-42" } };
        },
        get: async () => ({ data: { number: 42, node_id: "pull-42", auto_merge: null } }),
      },
    },
    graphql: async (_query, variables) => {
      calls.push(["enableAutoMerge", variables]);
    },
  };
  const core = {
    endGroup() {},
    error(message) {
      errors.push(message);
    },
    info() {},
    setFailed(message) {
      failures.push(message);
      throw new Error(message);
    },
    startGroup() {},
  };

  await run({ github, context: { repo: { owner: "acme", repo: "sisoc" } }, core });

  assert.deepEqual(calls, [
    ["closeLegacyPull", {
      owner: "acme",
      repo: "sisoc",
      pull_number: 41,
      state: "closed",
    }],
    ["createRef", {
      owner: "acme",
      repo: "sisoc",
      ref: "refs/heads/automation/sync-main-to-development",
      sha: "development-sha",
    }],
    ["merge", {
      owner: "acme",
      repo: "sisoc",
      base: "automation/sync-main-to-development",
      head: "development",
      commit_title: "chore(sync): incorporar development en automation/sync-main-to-development",
      commit_message: "Actualizacion segura de la rama temporal de sincronizacion descendente.",
    }],
    ["merge", {
      owner: "acme",
      repo: "sisoc",
      base: "automation/sync-main-to-development",
      head: "main",
      commit_title: "chore(sync): incorporar main en automation/sync-main-to-development",
      commit_message: "Actualizacion segura de la rama temporal de sincronizacion descendente.",
    }],
    ["createPull", {
      owner: "acme",
      repo: "sisoc",
      base: "development",
      head: "automation/sync-main-to-development",
      title: "chore(sync): integrar main en development",
      body: [
        "Sincronizacion descendente automatica.",
        "",
        "- La rama tecnica parte de la rama destino y solo incorpora `main`.",
        "- No escribe ni promueve cambios hacia `main`.",
        "- GitHub hace el merge solo cuando los requisitos de la ruleset estan verdes.",
      ].join("\n"),
    }],
    ["enableAutoMerge", { pullRequestId: "pull-42" }],
  ]);

  const callsBeforeInvalidResponse = calls.length;
  noContentResponse = { status: 201 };
  await assert.rejects(
    run({ github, context: { repo: { owner: "acme", repo: "sisoc" } }, core }),
    /respuesta inesperada.*status 201/i,
  );
  assert.match(errors.at(-1), /respuesta inesperada.*status 201/i);
  assert.match(failures.at(-1), /development: respuesta inesperada.*status 201/i);
  assert.deepEqual(
    calls.slice(callsBeforeInvalidResponse).map(([name]) => name),
    ["closeLegacyPull", "createRef", "merge"],
  );
});

test("nombra una rama tecnica aislada por destino", () => {
  assert.equal(
    synchronizationBranch("homologacion"),
    "automation/sync-main-to-homologacion",
  );
});
