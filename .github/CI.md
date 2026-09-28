# Research CI routing and dependency map

The repository has 21 workflows: 18 broadly triggered research workflows and
three workflows that already have path filters. This change keeps every original
job, platform matrix, command, artifact upload, permission, and research-branch
publication condition. The 18 broad workflows use the shared
[scope action](actions/research-scope/action.yml) after checkout and Python setup to avoid expensive
research steps when only these standalone documentation files change:

- `.github/README.md`
- `.github/CI.md`
- `CURRENT_REPRODUCTION.md`
- `graph_synthesis/DATASETS.md`

Every other path retains normal verification. In particular, **root `README.md`
and `REPRODUCE.md`, protocols, current results, and manuscript Markdown are research
inputs**. They must not be excluded by an extension such as `**/*.md`.

## Check names, failures, and comparison semantics

The existing jobs still start and report their original names, including each
Windows/Linux matrix context. On an allowlisted documentation change they perform
checkout, pinned Python setup, and classification; the two graph verification jobs also run the routing
regressions. Package installation, dataset download, scientific replay,
rendering, and artifact steps are skipped. This saves execution time while keeping
required checks satisfiable. It does not reduce the number of runner starts.

A workflow-level path filter can leave required checks pending. A job-level
condition runs before matrix expansion and can omit the platform-specific check
names. A replacement shared gate would change the set of check identities.
The local composite action retains the existing job identities without adding a
classification job to every workflow. See GitHub's
[workflow and matrix condition rules](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idif).

The [classifier](ci_scope.py) compares the PR head with its merge base using a
three-dot diff. Push events use the exact before/after trees with a two-dot diff.
Rename detection is disabled so a code file renamed into an allowlisted path
still includes its deleted source path. Deletions are included. The diff is not
limited to the first 300 files.

Existing checkout depths are retained. If comparison objects or ancestry are
missing from a shallow checkout, the classifier makes one bounded fetch from
`origin`: the two explicit commit refs, no tags, no blobs, depth 64 for PRs or
depth 1 for pushes, and a 45-second timeout. It logs the fetch depth and elapsed
seconds. Failure to fetch, insufficient ancestry, invalid event data, empty
diffs, new/deleted branches, and manual runs all retain normal verification.
If the action fails or its output is missing, the subsequent steps also run
normally. Existing `always()` failure-artifact conditions are preserved.

The main branch had no required-check protection or rulesets when reviewed on
2026-09-28. No protection is changed here. The three existing path-filtered
workflows below retain their original behavior; they should not be made required
for every PR without first providing an always-present check.

## Dependency matrix

All 18 **broad** rows run for any change outside the four-file allowlist, including
their own workflows and the routing implementation. Their input columns name
the checks' main dependency groups, not narrower path filters. This conservative
policy includes source, manifests, dataset acquisition, requirements, generators,
and stored evidence. Several report generators rebuild the cumulative manuscript
and invoke other studies; changing one study can affect another study's checks.

| Workflow and retained checks | Main inputs and unique verification | Routing |
| --- | --- | --- |
| [Graph synthesis](workflows/graph-synthesis.yml): `verify` on Windows/Linux | Original `MANIFEST.json` inventory; `reproduction/**`; dataset acquisition and hashes; core graph code/tests; `graph_synthesis.study`; numerical replay dependencies | Broad |
| [Graph figures](workflows/graph-figures.yml): `verify-figures` | `visualize_evidence.py`, saved observations, `evidence_figures/**`, core graph tests and figure dependencies; chart accounting and provenance | Broad |
| [Visual assessment](workflows/visual-assessment.yml): `figures-and-paper` | `visualize.py`, `render_paper.py`, original inventory, graph tests, illustration inputs and rendering dependencies | Broad |
| [Graph falsification](workflows/graph-falsification.yml): `falsification` on Windows/Linux | Graph core, falsification and semantic challenge code, evidence and original inventory; adversarial semantic checks | Broad |
| [Relationships](workflows/relationship-experiments.yml): `reproduce` on Windows/Linux | `experiments/relationships/**`, graph code/tests, saved evidence and numerical dependencies; journal/result reproduction | Broad |
| [Jev theory](workflows/jev-theory-suite.yml): `theory` on Windows/Linux | `graph_synthesis/theory_suite/**`, graph semantics; ten offline experiments and calibration/invariant tests | Broad |
| [Jev additional calls](workflows/jev-multicall.yml): `multicall` on Windows/Linux, `multicall-figures` | Saved multicall experiment, analysis/report modules, original inventory and all cumulative report sections | Broad |
| [Adaptive improvements](workflows/adaptive-improvements.yml): `replay` on Windows/Linux, `figures-and-paper` | `adaptive/**`, protocol/result/figure hashes, original inventory and cumulative manuscript | Broad |
| [Five improvements](workflows/research-followup.yml): `replay` on Windows/Linux, `paper-and-figures` | `followup/**`, corpus tests, falsification, original inventory and cumulative manuscript | Broad |
| [Risk control](workflows/risk-controlled-improvements.yml): `replay` on Windows/Linux, `figures-and-paper` | `risk_control/**`, offline controls, original inventory and cumulative manuscript | Broad |
| [Structural refinements](workflows/structural-refinements.yml): `replay` on Windows/Linux, `figures-and-paper` | `structural/**`, frozen artifacts, PDF provenance, original inventory and cumulative manuscript | Broad |
| [Source structure](workflows/source-structure.yml): `replay` on Windows/Linux, `figures-and-paper` | `source_structural/**`, provenance, original inventory and cumulative manuscript | Broad |
| [Reliability structure](workflows/reliability-structure.yml): `replay` on Windows/Linux, `figures-and-paper` | `reliability/**`, lifecycle checks, original inventory and cumulative manuscript | Broad |
| [Assumption awareness](workflows/assumption-aware.yml): `replay` on Windows/Linux, `figures-and-paper` | `assumption_aware/**`, independent oracle/artifact checks, original inventory and cumulative manuscript | Broad |
| [Structural frontier](workflows/structural-frontier.yml): `replay` on Windows/Linux, `figures-and-paper` | `frontier/**`, preceding structural/source/assumption studies, novel-mechanism sections, original inventory and cumulative manuscript | Broad |
| [New mechanisms](workflows/novel-mechanisms.yml): `replay` on Windows/Linux, `figures-and-paper` | `novel_mechanisms/**`, preceding-study regressions, publication/regret analyses, original inventory and cumulative manuscript | Broad |
| [Uncertainty](workflows/uncertainty-grounding.yml): `replay` on Windows/Linux, `figures-and-paper` | `uncertainty/**`, preceding-study preservation, original inventory and cumulative manuscript | Broad |
| [Dependence certificates](workflows/dependence-certificates.yml): `replay` | `certificates/**`, fixed protocol ancestry, numerical replay, original inventory and cumulative manuscript | Broad |
| [Corpus methodology](workflows/corpus-methodology.yml): Windows/Linux × Python 3.12/3.13 `offline-planning-tests` | `graph_synthesis/corpus/**`, `LARGE_CORPUS_METHODOLOGY.md`, own workflow; offline planning without model calls | Existing path filter |
| [DSPy optimizer](workflows/dspy-jev-optimizer.yml): Windows/Linux `offline`, `sdk-contracts` | `dspy_jev_optimizer/**`, own workflow; optimizer artifact/inventory checks, synthetic wiring, real SDKs with mocked inference | Existing path filter |
| [Post-certificate research](workflows/post-certificates.yml): `verify` | `post_certificates/**`, `CURRENT_RESULTS.md`, `manuscript/paper-current.*`, own workflow; protocol ancestry, numerical evidence, report/figure stability | Existing path filter |

The six existing `execute-and-publish` jobs remain confined to their original
research branches and conditions. This routing change does not enable live model
calls or introduce secrets.

## Measurements and validation

The documentation-only merge [PR #34](https://github.com/CompleteDotTech/paper-package/pull/34)
changed only `.github/README.md` at commit
`ad4a103a2f6072b892823dc581098d5b9650c057`. GitHub's completed job records show
18 workflow runs, 44 runner jobs, and **1,656 summed job execution seconds**.
The separate sum of workflow elapsed times was 1,435 seconds; it is not a runner
cost measurement because jobs within each workflow can overlap.

The new policy keeps those 44 status-producing jobs and routes all 44 away from
research execution for that exact diff. The comparison includes hosted checkout
and bounded-fetch overhead; execution time must be measured on the hosted
documentation probe, not inferred from the skipped commands.

Local validation commands:

```sh
python -B -m unittest discover -s .github -p test_ci_scope.py -v
actionlint -shellcheck= -pyflakes=
python -B -m graph_synthesis.verify
```

Routing tests use real Git repositories, including depth-one clones. They cover
PR and push comparisons, target-branch-only changes, renamed and deleted files,
frozen evidence and unknown paths, missing refs, insufficient fetch depth,
unavailable remotes, timeout, and missing event data. Routing tests run in both
graph-verification platform jobs even when the research steps are skipped.
