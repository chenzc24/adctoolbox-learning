# ADCToolbox Learner Wiki Rules

This wiki follows the LLM Wiki pattern from `../llm-wiki.md`, adapted for ADC,
mathematics, source-code learning, and engineering calibration rigor.

## Scope

This file governs only `toolbox-wiki/`.

Do not modify existing `adctoolbox-learning` files outside `toolbox-wiki/`
unless the user explicitly asks for that specific edit.

## Layers

### Raw Sources

Path: `toolbox-wiki/raw/`

Raw sources are immutable for wiki maintenance. The LLM may read them, cite
them, and create notes from them, but must not rewrite them.

### Wiki

Path: `toolbox-wiki/wiki/`

The wiki is the LLM-maintained synthesis layer. It contains concept pages,
source-code pages, workflow pages, rigor pages, and source notes.

### Schema

Path: `toolbox-wiki/schema/`

Schema files define conventions, page templates, and maintenance workflows.

### Logs

Path: `toolbox-wiki/logs/`

Logs are append-only. Every ingest, query-to-page conversion, lint pass, or
structural update should append an entry.

## Operating Modes

### Ingest

When ingesting a source:

1. Read the source.
2. Create or update a `wiki/source_notes/` page.
3. Update relevant `wiki/concepts/`, `wiki/source_code/`, `wiki/workflows/`, or `wiki/rigor/` pages.
4. Update `wiki/index.md`.
5. Append to `logs/log.md`.

Do not only summarize the source. Integrate it into the existing wiki.

Minimum ingest output for an important source:

- One source note in `wiki/source_notes/` or one source-code page in
  `wiki/source_code/`.
- At least one concept/workflow/rigor link.
- An updated `wiki/index.md` entry.
- A log entry.

If a source is only archived but not interpreted yet, mark it as `not-ingested`
in any relevant index or source note.

### Query

When answering a learning question:

1. Read `toolbox-wiki/index.md` and `wiki/index.md`.
2. Search relevant wiki pages first with `python tools/search_wiki.py <query>`
   or `rg`.
3. Read raw sources or ADCToolbox source code only when the wiki is insufficient.
4. If the answer creates reusable knowledge, offer to file it into the wiki.

Reusable answers include:

- A mathematical explanation.
- A source-code walkthrough.
- A comparison table.
- A validation checklist.
- A correction to a previous page.
- A newly identified open question.

### Lint

Periodic lint checks should look for:

- Pages without source links.
- Claims without rigor labels.
- Open questions without follow-up paths.
- Source-code pages not linked to concepts.
- Concept pages not linked to staged learning prerequisites.
- Contradictions between pages.
- Orphan pages not listed in `wiki/index.md`.

After manual review, run:

```bash
python tools/lint_wiki.py
```

The automated lint checks links, required metadata, index coverage, log heading
format, and raw directory presence. Passing automated lint does not replace
domain review; it only catches bookkeeping failures.

For conceptual review, use `schema/SEMANTIC_LINT_CHECKLIST.md`. Semantic lint
looks for contradictions, stale claims, semantic islands, weak evidence links,
and pages ready for promotion or demotion.

### Promotion

Use `schema/PROMOTION_RULES.md` before changing a page status. Status values
are:

- `draft`
- `usable`
- `stable`
- `deprecated`

Do not promote a page to `stable` unless it passes automated lint, semantic
lint, and has clear source/evidence support.

## Required Page Metadata

Every generated wiki page should include a metadata block:

```yaml
stage_link:
  - optional path to staged learning material
source_links:
  - source paths or code paths
rigor:
  - source-confirmed
status: draft
last_updated: YYYY-MM-DD
confidence: medium
```

Use one or more rigor labels:

- `source-confirmed`: directly confirmed by source code or source document.
- `example-verified`: demonstrated by an example script or test.
- `theory-supported`: follows from standard theory, but not fully proven in the project.
- `engineering-heuristic`: useful engineering rule or implementation choice.
- `open-question`: unresolved or requiring validation.

Use one confidence label:

- `high`: directly backed by source/code and no major unresolved caveat.
- `medium`: backed by source/code, but assumptions or scope matter.
- `low`: preliminary synthesis, needs checking.

## Claim Discipline

For ADC calibration and mathematics, every important claim must identify its
status:

- What is directly implemented?
- What is inferred?
- What assumptions are required?
- What remains unverified?

Avoid presenting a calibration result as engineering truth unless the page also
states validation scope, assumptions, and missing checks.

Every page that discusses calibration must explicitly separate:

- model equation,
- estimator or algorithm,
- assumptions,
- validation evidence,
- remaining engineering risks.

Every page that discusses metrics must explicitly state the FFT/window/binning
conditions needed for the metric to be meaningful.

## Page Naming

Use ASCII filenames for new wiki pages unless the user requests otherwise.
Chinese titles can appear inside the page.

Examples:

- `wiki/source_code/sar_py.md`
- `wiki/concepts/least_squares_adc_calibration.md`
- `wiki/rigor/identifiability_conditions.md`

## Links

Use relative Markdown links. Link to:

- Raw source notes.
- Existing staged learning material.
- ADCToolbox source files.
- Related concept, workflow, and rigor pages.

## Protection Rule

This wiki is additive. It must not swallow, reorganize, or overwrite the
existing staged learning course.

## Required Maintenance Files

Maintain these files:

- `wiki/index.md`: content catalog.
- `logs/log.md`: append-only operation history.
- `schema/LINT_CHECKLIST.md`: health-check procedure.
- `progress.md`: current learning state and protected boundaries.
- `coverage_matrix.md`: topic coverage map.
- `open_questions.md`: unresolved math, engineering, and maintenance queue.
- `tools/lint_wiki.py`: automated bookkeeping lint.
- `tools/search_wiki.py`: local keyword search for the wiki.
- `schema/PROMOTION_RULES.md`: page status and promotion rules.
- `schema/SEMANTIC_LINT_CHECKLIST.md`: conceptual health-check workflow.
- `schema/PROOF_PAGE_TEMPLATE.md`: template for mathematical rigor pages.
- `schema/EXAMPLE_NOTE_TEMPLATE.md`: template for example evidence notes.

## Source-Code Page Requirements

Every source-code page must include:

- direct source path,
- public API purpose,
- input/output shapes,
- core data flow,
- linked concepts,
- linked examples/tests when known,
- assumptions and rigor risks.

## Rigor Page Requirements

Every rigor page must include:

- the claim or risk,
- why it matters,
- what the current project does,
- what is not proven,
- how to test or validate it next.
