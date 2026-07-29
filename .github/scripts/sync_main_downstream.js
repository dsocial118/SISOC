"use strict";

const SYNCHRONIZATION_BRANCH_PREFIX = "automation/sync-main-to-";

function synchronizationBranch(target) {
  return `${SYNCHRONIZATION_BRANCH_PREFIX}${target}`;
}

function isAlreadyUpToDate(result) {
  return result.data.message === "Already up to date.";
}

async function ensureSynchronizationBranch({ github, owner, repo, target, branch }) {
  try {
    await github.rest.git.getRef({
      owner,
      repo,
      ref: `heads/${branch}`,
    });
    return;
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }
  }

  const targetRef = await github.rest.git.getRef({
    owner,
    repo,
    ref: `heads/${target}`,
  });
  await github.rest.git.createRef({
    owner,
    repo,
    ref: `refs/heads/${branch}`,
    sha: targetRef.data.object.sha,
  });
}

async function mergeIntoSynchronizationBranch({ github, owner, repo, branch, source }) {
  const merged = await github.rest.repos.merge({
    owner,
    repo,
    base: branch,
    head: source,
    commit_title: `chore(sync): incorporar ${source} en ${branch}`,
    commit_message: "Actualizacion segura de la rama temporal de sincronizacion descendente.",
  });

  if (!merged.data.merged && !isAlreadyUpToDate(merged)) {
    throw new Error(
      `No se pudo incorporar ${source} en ${branch}: ${merged.data.message}`,
    );
  }
}

async function enableAutoMerge({ github, core, pull }) {
  if (pull.auto_merge) {
    core.info(`PR #${pull.number} ya tiene auto-merge habilitado.`);
    return;
  }

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
  core.info(`PR #${pull.number} armado para auto-merge nativo.`);
}

async function closeLegacySynchronizationPulls({ github, core, owner, repo, target }) {
  const legacyPulls = await github.rest.pulls.list({
    owner,
    repo,
    state: "open",
    base: target,
    head: `${owner}:main`,
    per_page: 10,
  });
  const title = `chore(sync): integrar main en ${target}`;

  for (const pull of legacyPulls.data) {
    if (pull.user?.login !== "github-actions[bot]" || pull.title !== title) {
      continue;
    }
    await github.rest.pulls.update({
      owner,
      repo,
      pull_number: pull.number,
      state: "closed",
    });
    core.info(`PR directo obsoleto #${pull.number} cerrado a favor de la rama tecnica.`);
  }
}

async function synchronizeTarget({ github, core, owner, repo, target }) {
  const comparison = await github.rest.repos.compareCommits({
    owner,
    repo,
    base: "main",
    head: target,
  });
  if (comparison.data.behind_by === 0) {
    core.info(`${target} ya contiene todo main; no hay cambios.`);
    return;
  }

  const branch = synchronizationBranch(target);
  await closeLegacySynchronizationPulls({ github, core, owner, repo, target });
  await ensureSynchronizationBranch({ github, owner, repo, target, branch });
  await mergeIntoSynchronizationBranch({ github, owner, repo, branch, source: target });
  await mergeIntoSynchronizationBranch({ github, owner, repo, branch, source: "main" });

  const pulls = await github.rest.pulls.list({
    owner,
    repo,
    state: "open",
    base: target,
    head: `${owner}:${branch}`,
    per_page: 10,
  });
  let pull = pulls.data[0];
  if (!pull) {
    const created = await github.rest.pulls.create({
      owner,
      repo,
      base: target,
      head: branch,
      title: `chore(sync): integrar main en ${target}`,
      body: [
        "Sincronizacion descendente automatica.",
        "",
        "- La rama tecnica parte de la rama destino y solo incorpora `main`.",
        "- No escribe ni promueve cambios hacia `main`.",
        "- GitHub hace el merge solo cuando los requisitos de la ruleset estan verdes.",
      ].join("\n"),
    });
    pull = created.data;
    core.info(`PR #${pull.number} creado: ${pull.html_url}`);
  } else {
    core.info(`Reutilizando PR #${pull.number}: ${pull.html_url}`);
  }

  pull = (
    await github.rest.pulls.get({
      owner,
      repo,
      pull_number: pull.number,
    })
  ).data;
  await enableAutoMerge({ github, core, pull });
  core.info(
    `GitHub esperara CI y fusionara #${pull.number}; el push resultante activa el deploy del destino.`,
  );
}

async function run({ github, context, core }) {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const targets = ["development", "homologacion"];
  const failures = [];

  for (const target of targets) {
    core.startGroup(`Sincronizar main -> ${target}`);
    try {
      await synchronizeTarget({ github, core, owner, repo, target });
    } catch (error) {
      failures.push(`${target}: ${error.message}`);
      core.error(`${target}: ${error.stack ?? error.message}`);
    } finally {
      core.endGroup();
    }
  }

  if (failures.length > 0) {
    core.setFailed(failures.join("\n"));
  }
}

module.exports = {
  run,
  synchronizationBranch,
};
