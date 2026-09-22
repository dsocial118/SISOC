"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { promotionBranch, run } = require("./sync_main_downstream");

function fixture({ sourceSha = "a".repeat(40), behindBy = 1 } = {}) {
  const calls = [];
  const github = {
    rest: {
      git: {
        getRef: async ({ ref }) => {
          calls.push(["getRef", ref]);
          if (ref === "heads/main") return { data: { object: { sha: sourceSha } } };
          if (ref.startsWith("heads/automation/")) {
            const error = new Error("missing");
            error.status = 404;
            throw error;
          }
          return { data: { object: { sha: "b".repeat(40) } } };
        },
        createRef: async (payload) => calls.push(["createRef", payload]),
      },
      repos: {
        compareCommits: async (payload) => {
          calls.push(["compare", payload]);
          return { data: { behind_by: behindBy } };
        },
        merge: async (payload) => {
          calls.push(["merge", payload]);
          return { status: 201, data: { sha: "c".repeat(40) } };
        },
      },
      pulls: {
        list: async (payload) => {
          calls.push(["list", payload]);
          return { data: [] };
        },
        create: async (payload) => {
          calls.push(["create", payload]);
          return { data: { number: 7, node_id: "PR_7" } };
        },
        get: async () => ({ data: { number: 7, node_id: "PR_7", auto_merge: null } }),
      },
    },
    graphql: async (_query, variables) => calls.push(["autoMerge", variables]),
  };
  const notices = [];
  const core = { info() {}, notice: (message) => notices.push(message) };
  return { calls, core, github, notices, sourceSha };
}

test("promueve exactamente la revision desplegada mediante una rama tecnica", async () => {
  const { calls, core, github, sourceSha } = fixture();
  await run({
    github,
    core,
    context: { repo: { owner: "secretarianaf", repo: "SISOC" } },
    source: "main",
    target: "homologacion",
    deployedSha: sourceSha,
  });
  assert.equal(
    calls.filter(([name]) => name === "merge").at(-1)[1].head,
    sourceSha,
  );
  assert.deepEqual(calls.at(-1), ["autoMerge", { pullRequestId: "PR_7" }]);
});

test("no promueve si la rama fuente avanzo despues del deploy", async () => {
  const currentSha = "d".repeat(40);
  const { calls, core, github, notices } = fixture({ sourceSha: currentSha });
  await run({
    github,
    core,
    context: { repo: { owner: "secretarianaf", repo: "SISOC" } },
    source: "main",
    target: "homologacion",
    deployedSha: "a".repeat(40),
  });
  assert.equal(calls.some(([name]) => name === "merge"), false);
  assert.match(notices[0], /avanzo/);
});

test("usa una rama tecnica distinta para cada tramo", () => {
  assert.equal(
    promotionBranch("homologacion", "development"),
    "automation/promote-homologacion-to-development",
  );
});
