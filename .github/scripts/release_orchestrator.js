"use strict";

const REQUIRED_CHECKS = [
  "deploy_guard",
  "architecture_imports",
  "gitleaks",
  "sync_pr_artifacts",
];
const BASELINE_CHECK = "release_baseline";
const SUCCESSFUL_CONCLUSIONS = new Set(["success", "neutral", "skipped"]);
const FINAL_RELEASE_MARKER = /<!--\s*release-automation:\s*scheduled\s*-->/i;
const PREPARATION_RELEASE_MARKER = /<!--\s*release-final-pr:\s*(\d+)\s*-->/i;
const RELEASE_DATE_MARKER = /<!--\s*release-date:\s*(\d{4}-\d{2}-\d{2})\s*-->/i;
const RELEASE_HEAD_MARKER = /<!--\s*release-head:\s*([0-9a-f]{40})\s*-->/i;
const RELEASE_PREPARATION_MARKER =
  /<!--\s*release-preparation:\s*(pending|none|\d+)\s*-->/i;
const PREPARATION_BRANCH_PATTERN =
  /^codex\/predeploy-dev-main-\d{8}(?:-[a-z0-9-]+)?$/;

function markerMatch(body, marker) {
  return (body || "").match(marker);
}

function parsePreparationFinalNumber(body) {
  const match = markerMatch(body, PREPARATION_RELEASE_MARKER);
  const value = match ? Number.parseInt(match[1], 10) : null;
  return Number.isInteger(value) && value > 0 ? value : null;
}

function parseReleaseDate(body) {
  const match = markerMatch(body, RELEASE_DATE_MARKER);
  if (!match) {
    return null;
  }

  const value = match[1];
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    return null;
  }
  return value;
}

function parseReleaseHead(body) {
  const match = markerMatch(body, RELEASE_HEAD_MARKER);
  return match ? match[1].toLowerCase() : null;
}

function parseReleasePreparation(body) {
  const match = markerMatch(body, RELEASE_PREPARATION_MARKER);
  if (!match) {
    return null;
  }
  if (match[1].toLowerCase() === "pending" || match[1].toLowerCase() === "none") {
    return match[1].toLowerCase();
  }
  const value = Number.parseInt(match[1], 10);
  return Number.isInteger(value) && value > 0 ? value : null;
}

function stableTagName(releaseDate) {
  return `${releaseDate.replaceAll("-", ".")}-stable`;
}

function isReleaseSnapshotCurrent(pull) {
  return parseReleaseHead(pull.body) === (pull.head?.sha || "").toLowerCase();
}

function isInternalPullRequest(pull, repositoryFullName) {
  return pull.head?.repo?.full_name === repositoryFullName;
}

function isPreparationPullRequest(pull, repositoryFullName) {
  return (
    pull.base?.ref === "development" &&
    isInternalPullRequest(pull, repositoryFullName) &&
    PREPARATION_BRANCH_PATTERN.test(pull.head?.ref || "") &&
    parsePreparationFinalNumber(pull.body) !== null
  );
}

function isScheduledFinalPullRequest(pull, repositoryFullName) {
  return (
    pull.base?.ref === "main" &&
    pull.head?.ref === "development" &&
    isInternalPullRequest(pull, repositoryFullName) &&
    FINAL_RELEASE_MARKER.test(pull.body || "") &&
    parseReleaseDate(pull.body) !== null &&
    parseReleaseHead(pull.body) !== null &&
    parseReleasePreparation(pull.body) !== null
  );
}

function newestCheckRuns(checkRuns) {
  const byName = new Map();
  for (const check of checkRuns) {
    const current = byName.get(check.name);
    const checkTimestamp = Date.parse(check.completed_at || check.started_at || "") || 0;
    const currentTimestamp = current
      ? Date.parse(current.completed_at || current.started_at || "") || 0
      : -1;
    if (!current || checkTimestamp >= currentTimestamp) {
      byName.set(check.name, check);
    }
  }
  return byName;
}

function requiredChecksState(checkRuns, requiredChecks = REQUIRED_CHECKS) {
  const latest = newestCheckRuns(checkRuns);
  const pending = [];
  const failed = [];

  for (const name of requiredChecks) {
    const check = latest.get(name);
    if (!check || check.status !== "completed") {
      pending.push(name);
      continue;
    }
    if (!SUCCESSFUL_CONCLUSIONS.has(check.conclusion)) {
      failed.push(`${name} (${check.conclusion || "unknown"})`);
    }
  }

  return { pending, failed };
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function getPull(github, owner, repo, pullNumber) {
  const response = await github.rest.pulls.get({
    owner,
    repo,
    pull_number: pullNumber,
  });
  return response.data;
}

async function getCheckRuns(github, owner, repo, sha) {
  const response = await github.rest.checks.listForRef({
    owner,
    repo,
    ref: sha,
    per_page: 100,
  });
  return response.data.check_runs;
}

async function getRequiredChecksState(github, owner, repo, sha) {
  return requiredChecksState(await getCheckRuns(github, owner, repo, sha));
}

async function commentOnce(github, owner, repo, issueNumber, marker, body) {
  const comments = await github.rest.issues.listComments({
    owner,
    repo,
    issue_number: issueNumber,
    per_page: 100,
  });
  if (comments.data.some((comment) => (comment.body || "").includes(marker))) {
    return;
  }
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: issueNumber,
    body: `${marker}\n${body}`,
  });
}

async function markFinalPullRequestReady(github, owner, repo, pullNumber, core) {
  let pull = await getPull(github, owner, repo, pullNumber);
  const repositoryFullName = `${owner}/${repo}`;
  if (!isScheduledFinalPullRequest(pull, repositoryFullName)) {
    throw new Error(
      `PR #${pullNumber} no es una promocion programada valida development -> main.`,
    );
  }

  if (pull.draft) {
    await github.graphql(
      `mutation MarkReady($pullRequestId: ID!) {
        markPullRequestReadyForReview(input: { pullRequestId: $pullRequestId }) {
          pullRequest { id isDraft }
        }
      }`,
      { pullRequestId: pull.node_id },
    );
    core.info(`PR final #${pull.number} marcado como listo para auto-merge.`);
    pull = await getPull(github, owner, repo, pullNumber);
  }
  return pull;
}

async function setFinalReleaseHead(github, owner, repo, pullNumber, headSha, core) {
  const pull = await getPull(github, owner, repo, pullNumber);
  const repositoryFullName = `${owner}/${repo}`;
  if (!isScheduledFinalPullRequest(pull, repositoryFullName)) {
    throw new Error(
      `PR #${pullNumber} no es una promocion programada valida development -> main.`,
    );
  }

  const body = pull.body || "";
  const updatedBody = RELEASE_HEAD_MARKER.test(body)
    ? body.replace(RELEASE_HEAD_MARKER, `<!-- release-head: ${headSha} -->`)
    : `${body.trim()}\n\n<!-- release-head: ${headSha} -->\n`;
  if (updatedBody === body) {
    return pull;
  }
  const updated = await github.rest.pulls.update({
    owner,
    repo,
    pull_number: pullNumber,
    body: updatedBody,
  });
  core.info(`PR final #${pullNumber} actualizado al snapshot ${headSha}.`);
  return updated.data;
}

async function ensureBaselinePending(github, owner, repo, pull, core) {
  const externalId = `release-baseline:${pull.number}:${pull.base.sha}:${pull.head.sha}`;
  const latest = newestCheckRuns(await getCheckRuns(github, owner, repo, pull.head.sha));
  const existing = latest.get(BASELINE_CHECK);
  if (
    existing
    && existing.external_id === externalId
    && (
      existing.status !== "completed"
      || existing.conclusion === "success"
    )
  ) {
    return existing;
  }

  const created = await github.rest.checks.create({
    owner,
    repo,
    name: BASELINE_CHECK,
    head_sha: pull.head.sha,
    status: "in_progress",
    external_id: externalId,
    output: {
      title: "Baseline de rollback pendiente",
      summary: "La promoción espera el tag del main previo y la validación final de release.",
    },
  });
  core.info(`Check ${BASELINE_CHECK} creado para PR #${pull.number}.`);
  return created.data;
}

async function concludeBaseline(
  github,
  owner,
  repo,
  pull,
  conclusion,
  title,
  summary,
  core,
) {
  const check = await ensureBaselinePending(github, owner, repo, pull, core);
  if (check.status === "completed" && check.conclusion === conclusion) {
    return check;
  }
  const updated = await github.rest.checks.update({
    owner,
    repo,
    check_run_id: check.id,
    status: "completed",
    conclusion,
    output: { title, summary },
  });
  return updated.data;
}

async function enableAutoMerge(github, pull, core) {
  if (pull.auto_merge) {
    return true;
  }
  try {
    await github.graphql(
      `mutation EnableAutoMerge($pullRequestId: ID!) {
        enablePullRequestAutoMerge(
          input: { pullRequestId: $pullRequestId, mergeMethod: MERGE }
        ) {
          pullRequest { autoMergeRequest { enabledAt mergeMethod } }
        }
      }`,
      { pullRequestId: pull.node_id },
    );
    core.info(`Auto-merge nativo habilitado para PR #${pull.number}.`);
    return true;
  } catch (error) {
    core.warning(
      `No se pudo habilitar auto-merge para PR #${pull.number}: ${error.message}`,
    );
    return false;
  }
}

async function disableAutoMerge(github, pull, core) {
  if (!pull.auto_merge) {
    return;
  }
  try {
    await github.graphql(
      `mutation DisableAutoMerge($pullRequestId: ID!) {
        disablePullRequestAutoMerge(input: { pullRequestId: $pullRequestId }) {
          pullRequest { autoMergeRequest { enabledAt } }
        }
      }`,
      { pullRequestId: pull.node_id },
    );
    core.info(`Auto-merge deshabilitado para PR #${pull.number}.`);
  } catch (error) {
    core.warning(
      `No se pudo deshabilitar auto-merge para PR #${pull.number}: ${error.message}`,
    );
  }
}

async function getTagTarget(github, owner, repo, tagName) {
  try {
    const ref = await github.rest.git.getRef({
      owner,
      repo,
      ref: `tags/${tagName}`,
    });
    if (ref.data.object.type === "tag") {
      const tag = await github.rest.git.getTag({
        owner,
        repo,
        tag_sha: ref.data.object.sha,
      });
      return tag.data.object.sha;
    }
    return ref.data.object.sha;
  } catch (error) {
    if (error.status === 404) {
      return null;
    }
    throw error;
  }
}

async function ensureStableTag(github, owner, repo, tagName, mainSha, pullNumber) {
  const existingTarget = await getTagTarget(github, owner, repo, tagName);
  if (existingTarget) {
    if (existingTarget !== mainSha) {
      throw new Error(
        `El tag ${tagName} ya apunta a ${existingTarget}, no al main actual ${mainSha}.`,
      );
    }
    return { created: false, target: existingTarget };
  }

  const tag = await github.rest.git.createTag({
    owner,
    repo,
    tag: tagName,
    message: [
      `Stable release ${tagName.replace("-stable", "")}`,
      "",
      `Baseline de rollback anterior a la promocion del PR #${pullNumber}.`,
    ].join("\n"),
    object: mainSha,
    type: "commit",
    tagger: {
      name: "github-actions[bot]",
      email: "41898282+github-actions[bot]@users.noreply.github.com",
      date: new Date().toISOString(),
    },
  });

  try {
    await github.rest.git.createRef({
      owner,
      repo,
      ref: `refs/tags/${tagName}`,
      sha: tag.data.sha,
    });
    return { created: true, target: mainSha };
  } catch (error) {
    if (error.status !== 422) {
      throw error;
    }
    const racedTarget = await getTagTarget(github, owner, repo, tagName);
    if (racedTarget === mainSha) {
      return { created: false, target: racedTarget };
    }
    throw new Error(`No se pudo crear el tag estable ${tagName} de forma segura.`);
  }
}

async function removeFreshStableTag(github, owner, repo, tagName) {
  await github.rest.git.deleteRef({
    owner,
    repo,
    ref: `tags/${tagName}`,
  });
}

async function ensureStableRelease(
  github,
  owner,
  repo,
  tagName,
  mainSha,
  pullNumber,
) {
  try {
    const existing = await github.rest.repos.getReleaseByTag({
      owner,
      repo,
      tag: tagName,
    });
    return existing.data.html_url;
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }
  }

  try {
    const created = await github.rest.repos.createRelease({
      owner,
      repo,
      tag_name: tagName,
      target_commitish: mainSha,
      name: `Rollback baseline ${tagName}`,
      body: [
        `Baseline de rollback anterior a la promoción del PR #${pullNumber}.`,
        `Main previo: ${mainSha}.`,
      ].join("\n"),
      draft: false,
      prerelease: false,
      generate_release_notes: false,
    });
    return created.data.html_url;
  } catch (error) {
    if (error.status !== 422) {
      throw error;
    }
    const raced = await github.rest.repos.getReleaseByTag({
      owner,
      repo,
      tag: tagName,
    });
    return raced.data.html_url;
  }
}

async function blockFinal(github, owner, repo, pull, reason, core) {
  await disableAutoMerge(github, pull, core);
  if (!pull.draft) {
    await concludeBaseline(
      github,
      owner,
      repo,
      pull,
      "failure",
      "Promoción bloqueada",
      reason,
      core,
    );
  }
  await commentOnce(
    github,
    owner,
    repo,
    pull.number,
    "<!-- release-final-blocked -->",
    reason,
  );
}

async function armFinalForAutoMerge(github, owner, repo, pullNumber, core) {
  let pull = await markFinalPullRequestReady(github, owner, repo, pullNumber, core);
  if (!isReleaseSnapshotCurrent(pull)) {
    await blockFinal(
      github,
      owner,
      repo,
      pull,
      "El head de `development` cambió después del snapshot analizado. Se requiere una nueva ejecución de pre-deploy.",
      core,
    );
    return false;
  }
  await ensureBaselinePending(github, owner, repo, pull, core);
  pull = await getPull(github, owner, repo, pullNumber);
  return enableAutoMerge(github, pull, core);
}

async function processDraftFinalPullRequests(github, owner, repo, core) {
  const repositoryFullName = `${owner}/${repo}`;
  const pulls = await github.rest.pulls.list({
    owner,
    repo,
    state: "open",
    base: "main",
    per_page: 100,
  });

  for (const item of pulls.data) {
    const pull = await getPull(github, owner, repo, item.number);
    if (!isScheduledFinalPullRequest(pull, repositoryFullName) || !pull.draft) {
      continue;
    }

    const preparation = parseReleasePreparation(pull.body);
    if (preparation === "pending") {
      continue;
    }
    if (preparation === "none") {
      await armFinalForAutoMerge(github, owner, repo, pull.number, core);
      continue;
    }

    const preparationPull = await getPull(github, owner, repo, preparation);
    if (!preparationPull.merged || !preparationPull.merge_commit_sha) {
      continue;
    }
    await setFinalReleaseHead(
      github,
      owner,
      repo,
      pull.number,
      preparationPull.merge_commit_sha,
      core,
    );
    await armFinalForAutoMerge(github, owner, repo, pull.number, core);
  }
}

async function processReadyFinalPullRequests(github, owner, repo, core) {
  const repositoryFullName = `${owner}/${repo}`;
  const pulls = await github.rest.pulls.list({
    owner,
    repo,
    state: "open",
    base: "main",
    per_page: 100,
  });

  for (const item of pulls.data) {
    let pull = await getPull(github, owner, repo, item.number);
    if (!isScheduledFinalPullRequest(pull, repositoryFullName) || pull.draft) {
      continue;
    }

    if (!isReleaseSnapshotCurrent(pull)) {
      await blockFinal(
        github,
        owner,
        repo,
        pull,
        "El head de `development` cambió después del snapshot analizado. Se requiere una nueva ejecución de pre-deploy.",
        core,
      );
      continue;
    }

    const checks = await getRequiredChecksState(github, owner, repo, pull.head.sha);
    if (checks.pending.length > 0) {
      core.info(`PR final #${pull.number}: checks pendientes (${checks.pending.join(", ")}).`);
      continue;
    }
    if (checks.failed.length > 0) {
      await blockFinal(
        github,
        owner,
        repo,
        pull,
        `La promoción automática queda bloqueada: ${checks.failed.join(", ")}.`,
        core,
      );
      continue;
    }

    const comparison = await github.rest.repos.compareCommits({
      owner,
      repo,
      base: "main",
      head: "development",
    });
    if (comparison.data.behind_by !== 0) {
      core.info(
        `PR final #${pull.number}: development aún no contiene el main más nuevo; se espera la sincronización descendente.`,
      );
      continue;
    }

    await ensureBaselinePending(github, owner, repo, pull, core);
    pull = await getPull(github, owner, repo, pull.number);
    if (!isReleaseSnapshotCurrent(pull)) {
      await blockFinal(
        github,
        owner,
        repo,
        pull,
        "El head cambió mientras se armaba el baseline de rollback.",
        core,
      );
      continue;
    }

    const mainBeforeMerge = await github.rest.repos.getBranch({
      owner,
      repo,
      branch: "main",
    });
    const tagName = stableTagName(parseReleaseDate(pull.body));
    const stableTag = await ensureStableTag(
      github,
      owner,
      repo,
      tagName,
      mainBeforeMerge.data.commit.sha,
      pull.number,
    );

    const refreshedMain = await github.rest.repos.getBranch({
      owner,
      repo,
      branch: "main",
    });
    const pullAtGate = await getPull(github, owner, repo, pull.number);
    if (
      refreshedMain.data.commit.sha !== mainBeforeMerge.data.commit.sha
      || pullAtGate.base.sha !== mainBeforeMerge.data.commit.sha
      || pullAtGate.head.sha !== pull.head.sha
      || !isReleaseSnapshotCurrent(pullAtGate)
    ) {
      if (stableTag.created) {
        await removeFreshStableTag(github, owner, repo, tagName);
      }
      core.info(`PR final #${pull.number}: base o head cambió antes de liberar el baseline.`);
      continue;
    }

    const stableUrl = await ensureStableRelease(
      github,
      owner,
      repo,
      tagName,
      stableTag.target,
      pull.number,
    );

    await concludeBaseline(
      github,
      owner,
      repo,
      pullAtGate,
      "success",
      "Baseline de rollback listo",
      `Tag: ${tagName}. Main previo: ${stableTag.target}. ${stableUrl}`,
      core,
    );
    await enableAutoMerge(github, pullAtGate, core);
    core.info(`PR final #${pull.number} listo para que GitHub complete el auto-merge.`);
  }
}

async function reportFinalMerge(github, owner, repo, pull, core) {
  const releaseDate = parseReleaseDate(pull.body);
  if (!releaseDate) {
    return;
  }
  const tagName = stableTagName(releaseDate);
  let stableUrl = `https://github.com/${owner}/${repo}/tree/${tagName}`;
  try {
    const release = await github.rest.repos.getReleaseByTag({
      owner,
      repo,
      tag: tagName,
    });
    stableUrl = release.data.html_url;
  } catch (error) {
    core.warning(`No se encontró release para ${tagName}: ${error.message}`);
  }
  await commentOnce(
    github,
    owner,
    repo,
    pull.number,
    "<!-- release-final-merged -->",
    [
      `Promoción integrada en main: ${pull.merge_commit_sha || "SHA no informado"}.`,
      `Tag de rollback: [${tagName}](${stableUrl}).`,
      "El deploy queda pendiente de la aprobación del Environment production para el SHA vigente.",
    ].join("\n"),
  );
}

async function run({ github, context, core }) {
  const { owner, repo } = context.repo;

  if (context.eventName === "pull_request") {
    const pull = context.payload.pull_request;
    const repositoryFullName = `${owner}/${repo}`;
    if (pull?.merged && isPreparationPullRequest(pull, repositoryFullName)) {
      const finalNumber = parsePreparationFinalNumber(pull.body);
      if (!pull.merge_commit_sha) {
        throw new Error(`PR de preparación #${pull.number} no informa merge_commit_sha.`);
      }
      const finalPull = await getPull(github, owner, repo, finalNumber);
      if (parseReleasePreparation(finalPull.body) !== pull.number) {
        core.warning(
          `PR de preparación #${pull.number} no coincide con el marker del PR final #${finalNumber}.`,
        );
        return;
      }
      await setFinalReleaseHead(github, owner, repo, finalNumber, pull.merge_commit_sha, core);
      await armFinalForAutoMerge(github, owner, repo, finalNumber, core);
      return;
    }
    if (pull?.merged && isScheduledFinalPullRequest(pull, repositoryFullName)) {
      await reportFinalMerge(github, owner, repo, pull, core);
    }
    return;
  }

  if (context.eventName === "workflow_dispatch") {
    const finalNumber = Number.parseInt(context.payload.inputs?.release_pr || "", 10);
    if (!Number.isInteger(finalNumber) || finalNumber <= 0) {
      throw new Error("workflow_dispatch requiere el input release_pr con el PR final.");
    }
    await armFinalForAutoMerge(github, owner, repo, finalNumber, core);
    await processReadyFinalPullRequests(github, owner, repo, core);
    return;
  }

  if (context.eventName === "workflow_run" || context.eventName === "schedule") {
    await processDraftFinalPullRequests(github, owner, repo, core);
    await processReadyFinalPullRequests(github, owner, repo, core);
  }
}

module.exports = {
  BASELINE_CHECK,
  FINAL_RELEASE_MARKER,
  PREPARATION_BRANCH_PATTERN,
  REQUIRED_CHECKS,
  isPreparationPullRequest,
  isReleaseSnapshotCurrent,
  isScheduledFinalPullRequest,
  parsePreparationFinalNumber,
  parseReleaseDate,
  parseReleaseHead,
  parseReleasePreparation,
  requiredChecksState,
  run,
  stableTagName,
};
