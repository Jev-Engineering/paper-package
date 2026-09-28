# Research CI routing and dependency map

The repository has 21 research workflows: 18 broadly triggered workflows and
three workflows that already have path filters. The 18 broad workflows now use
`paths-ignore` on both pull requests and pushes for exactly four standalone docs:

- `.github/README.md`
- `.github/CI.md`
- `CURRENT_REPRODUCTION.md`
- `graph_synthesis/DATASETS.md`

A change confined to those files runs one lightweight
[documentation workflow](workflows/documentation.yml), which checks their local
link destinations without network access or third-party Python dependencies.
That workflow also runs when its own implementation changes. Research jobs,
platform matrices, commands, artifact uploads, permissions, and research-branch
publication conditions are retained unchanged for relevant changes.

Every other path retains normal research verification. **Root `README.md` and
`REPRODUCE.md`, protocols, current results, and manuscript Markdown are research
inputs**. They must not be excluded using a broad glob such as `**/*.md`.
Mixed documentation/source changes and edits to any workflow run the research
workflows. No custom classifier, extra scope jobs, deep fetch, or API call is
needed: GitHub evaluates these exact path filters before assigning runners.

## Required checks and filter boundaries

The main branch had no required-check protection or rulesets when reviewed on
2026-09-28. No protection or existing check name is changed here. A workflow
excluded by a native path filter does not report its usual check contexts.
Before introducing required checks, maintainers must account for these filters:
requiring a conditional research job for every PR can leave a docs-only PR
pending. Either require checks only for their applicable changes or introduce an
always-present gate that validates the intended routing and results. The same
consideration already applies to the three previously scoped research workflows.
See GitHub's [path-filter documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onpushpull_requestpull_request_targetpathspaths-ignore).

GitHub uses a three-dot diff for pull requests and a two-dot diff for existing
branch pushes. Because the ignore set contains only four literal file paths,
this change cannot hide a research input behind a broad Markdown or directory
pattern. New workflow files and all shared code/evidence still trigger the broad
workflows. A manual run retains the workflow's existing full behavior.

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
| [Corpus methodology](workflows/corpus-methodology.yml): Windows/Linux Ã— Python 3.12/3.13 `offline-planning-tests` | `graph_synthesis/corpus/**`, `LARGE_CORPUS_METHODOLOGY.md`, own workflow; offline planning without model calls | Existing path filter |
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

For that same changed-file set, the native filters select only the documentation
workflow: **44 research jobs become one documentation-link job**. Source,
requirements, dataset acquisition, manifest, stored evidence, rendering, and
workflow changes retain all 44 original broad-workflow jobs, plus any applicable
previously scoped workflow. A change to this routing implementation runs the full
research collection and the documentation check.

Validate routing against both event blocks and the complete workflow definitions;
verify that only the four literal standalone paths are ignored and that every
original job definition is unchanged. Validate examples for a single standalone
doc, several standalone docs, a mixed doc/code change, root archival Markdown,
current manuscripts, shared code, requirements, datasets, and workflow edits.
Measure the hosted documentation-only probe before claiming runtime savings.

Local validation commands:

```sh
python -B -m unittest discover -s .github -p test_documentation.py -v
python -B .github/check_documentation.py
actionlint -shellcheck= -pyflakes=
python -B -m graph_synthesis.verify
```

The documentation checker validates local file/directory destinations in ordinary
Markdown links. It ignores external URLs, fragment-only links, and fenced examples;
it does not crawl remote websites or claim to validate generated heading anchors.
