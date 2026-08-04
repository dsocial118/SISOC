"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const orchestrator = require("./release_orchestrator");

const repositoryFullName = "dsocial118/SISOC";

function pull(overrides = {}) {
  return {
    base: { ref: "main" },
    head: { ref: "development", repo: { full_name: repositoryFullName } },
    body: [
      "<!-- release-automation: scheduled -->",
      "<!-- release-date: 2026-07-29 -->",
      "<!-- release-head: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -->",
      "<!-- release-preparation: none -->",
    ].join("\n"),
    ...overrides,
  };
}

test("reconoce un PR final programado y deriva su tag estable", () => {
  const finalPull = pull({
    head: {
      ref: "development",
      sha: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      repo: { full_name: repositoryFullName },
    },
  });

  assert.equal(
    orchestrator.isScheduledFinalPullRequest(finalPull, repositoryFullName),
    true,
  );
  assert.equal(orchestrator.parseReleaseDate(finalPull.body), "2026-07-29");
  assert.equal(
    orchestrator.parseReleaseHead(finalPull.body),
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  );
  assert.equal(orchestrator.isReleaseSnapshotCurrent(finalPull), true);
  assert.equal(orchestrator.stableTagName("2026-07-29"), "2026.07.29-stable");
});

test("rechaza PRs finales que no tienen fecha de release valida", () => {
  const invalid = pull({ body: "<!-- release-automation: scheduled -->\n<!-- release-date: 2026-02-31 -->\n<!-- release-head: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -->" });

  assert.equal(orchestrator.parseReleaseDate(invalid.body), null);
  assert.equal(
    orchestrator.isScheduledFinalPullRequest(invalid, repositoryFullName),
    false,
  );
});

test("rechaza un PR final sin el SHA exacto del snapshot", () => {
  const missingHead = pull({
    body: "<!-- release-automation: scheduled -->\n<!-- release-date: 2026-07-29 -->",
  });

  assert.equal(
    orchestrator.isScheduledFinalPullRequest(missingHead, repositoryFullName),
    false,
  );
});

test("acepta los estados controlados de preparación", () => {
  assert.equal(orchestrator.parseReleasePreparation("<!-- release-preparation: pending -->"), "pending");
  assert.equal(orchestrator.parseReleasePreparation("<!-- release-preparation: none -->"), "none");
  assert.equal(orchestrator.parseReleasePreparation("<!-- release-preparation: 2140 -->"), 2140);
});

test("detecta cuando development avanzó después del snapshot", () => {
  const stale = pull({
    head: {
      ref: "development",
      sha: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      repo: { full_name: repositoryFullName },
    },
  });

  assert.equal(orchestrator.isReleaseSnapshotCurrent(stale), false);
});

test("solo habilita preparaciones internas con el prefijo controlado", () => {
  const preparation = pull({
    base: { ref: "development" },
    head: {
      ref: "codex/predeploy-dev-main-20260729",
      repo: { full_name: repositoryFullName },
    },
    body: "<!-- release-final-pr: 2140 -->",
  });

  assert.equal(orchestrator.parsePreparationFinalNumber(preparation.body), 2140);
  assert.equal(
    orchestrator.isPreparationPullRequest(preparation, repositoryFullName),
    true,
  );
  assert.equal(
    orchestrator.isPreparationPullRequest(
      pull({
        base: { ref: "development" },
        head: { ref: "feature/unsafe", repo: { full_name: repositoryFullName } },
        body: "<!-- release-final-pr: 2140 -->",
      }),
      repositoryFullName,
    ),
    false,
  );
});

test("clasifica checks faltantes, pendientes y fallidos", () => {
  const checks = [
    { name: "deploy_guard", status: "completed", conclusion: "success" },
    { name: "architecture_imports", status: "in_progress", conclusion: null },
    { name: "gitleaks", status: "completed", conclusion: "success" },
    { name: "sync_pr_artifacts", status: "completed", conclusion: "failure" },
  ];

  assert.deepEqual(orchestrator.requiredChecksState(checks), {
    pending: ["architecture_imports"],
    failed: ["sync_pr_artifacts (failure)"],
  });
});
