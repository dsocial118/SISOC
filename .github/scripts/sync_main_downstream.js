"use strict";

const PROMOTION_BRANCH_PREFIX = "automation/promote-";

function promotionBranch(source, target) {
  return `${PROMOTION_BRANCH_PREFIX}${source}-to-${target}`;
}

function isCommitSha(value) {
  return typeof value === "string" && /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/i.test(value);
}

async function ensurePromotionBranch({ github, owner, repo, target, branch }) {
  try {
    await github.rest.git.getRef({ owner, repo, ref: `heads/${branch}` });
    return;
  } catch (error) {
    if (error.status !== 404) throw error;
  }

  const targetRef = await github.rest.git.getRef({ owner, repo, ref: `heads/${target}` });
  await github.rest.git.createRef({
    owner,
    repo,
    ref: `refs/heads/${branch}`,
    sha: targetRef.data.object.sha,
  });
}

async function mergeIntoPromotionBranch({ github, owner, repo, branch, head }) {
  const merged = await github.rest.repos.merge({
    owner,
    repo,
    base: branch,
    head,
    commit_title: `chore(sync): incorporar ${head} en ${branch}`,
    commit_message: "Promocion descendente posterior a un despliegue verificado.",
  });
  if (merged?.status === 204 && merged.data == null) return;
  if (merged?.status === 201 && isCommitSha(merged.data?.sha)) return;
  const detail = merged?.data?.message
    ?? (merged?.data ? "falta SHA valido del commit resultante" : "falta cuerpo");
  throw new Error(`Respuesta inesperada al incorporar ${head}: ${detail} (status ${merged?.status ?? "desconocido"}).`);
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
}

async function run({ github, context, core, source, target, deployedSha }) {
  if (!source || !target || source === target || !isCommitSha(deployedSha)) {
    throw new Error("Parametros de promocion invalidos.");
  }
  const { owner, repo } = context.repo;
  const sourceRef = await github.rest.git.getRef({ owner, repo, ref: `heads/${source}` });
  if (sourceRef.data.object.sha !== deployedSha) {
    core.notice(
      `No se promueve ${deployedSha}: ${source} avanzo a ${sourceRef.data.object.sha}.`,
    );
    return;
  }

  const comparison = await github.rest.repos.compareCommits({
    owner,
    repo,
    base: deployedSha,
    head: target,
  });
  if (comparison.data.behind_by === 0) {
    core.info(`${target} ya contiene la revision desplegada ${deployedSha}.`);
    return;
  }

  const branch = promotionBranch(source, target);
  await ensurePromotionBranch({ github, owner, repo, target, branch });
  await mergeIntoPromotionBranch({ github, owner, repo, branch, head: target });
  await mergeIntoPromotionBranch({ github, owner, repo, branch, head: deployedSha });

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
    pull = (
      await github.rest.pulls.create({
        owner,
        repo,
        base: target,
        head: branch,
        title: `chore(sync): integrar ${source} en ${target}`,
        body: [
          "Promocion descendente automatica.",
          "",
          `- Revision ya desplegada en \`${source}\`: \`${deployedSha}\`.`,
          `- Destino: \`${target}\`.`,
          "- GitHub fusiona solo cuando la ruleset y los checks requeridos estan verdes.",
        ].join("\n"),
      })
    ).data;
  }
  pull = (
    await github.rest.pulls.get({ owner, repo, pull_number: pull.number })
  ).data;
  await enableAutoMerge({ github, core, pull });
  core.info(`PR #${pull.number} preparado para promover ${source} -> ${target}.`);
}

module.exports = { run, promotionBranch };
