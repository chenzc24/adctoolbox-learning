# Page Promotion Rules

These rules define when a generated wiki page can move from `draft` to
`usable` to `stable`.

## Status Levels

### draft

Use `draft` for first-pass pages.

Minimum requirements:

- Metadata block exists.
- `source_links` exists.
- `rigor` labels exist.
- `last_updated` exists.
- The page is listed in `wiki/index.md`.

### usable

Use `usable` when a page is safe to cite during normal learning sessions.

Requirements:

- All `draft` requirements pass.
- `python tools/lint_wiki.py` passes.
- The page links to at least two related wiki pages.
- The page has at least one direct source, code, or raw-source note.
- Important claims are separated into implemented facts, assumptions, and open
  questions.
- The page states what it does not prove.
- If the page is a source-code page, it links to at least one concept page.
- If the page is a concept page, it links to at least one source-code,
  workflow, source-note, or rigor page.

### stable

Use `stable` when a page can serve as a long-lived reference.

Requirements:

- All `usable` requirements pass.
- The page has survived at least one semantic lint pass.
- Related `open_questions.md` items are closed, linked as partial answers, or
  explicitly deferred.
- The page has no unresolved contradiction with related pages.
- At least one example, source note, code path, or validation recipe supports
  the page.
- The page has a clear maintenance path: what should update it, and what would
  invalidate it.

## Extra Requirements By Page Type

### Source-code pages

- Name public APIs or internal helper APIs.
- State input and output shapes.
- State core data flow.
- Link to examples or say that example notes are not yet ingested.
- State implementation risks and assumptions.

### Concept pages

- Define the concept in learner language.
- Link to code where the concept appears.
- Link to raw/source notes that motivated the concept.
- Include at least one misuse or failure mode.

### Workflow pages

- Give an executable sequence of operations.
- State entry conditions and expected outputs.
- Link to the relevant concept, source-code, and rigor pages.
- State validation evidence and residual risks.

### Rigor pages

- State the claim, model, assumptions, and failure modes.
- Separate proven facts from engineering heuristics.
- Include a validation recipe.
- Keep unresolved proof obligations linked from `open_questions.md`.

### Source notes

- Link to the raw source.
- Extract reusable ideas rather than merely summarizing.
- Link to the concept/source-code/workflow/rigor pages affected by the source.
- State what the source does not resolve.

## Promotion Workflow

1. Read the candidate page and related pages.
2. Run `python tools/lint_wiki.py`.
3. Run the semantic lint checklist in `schema/SEMANTIC_LINT_CHECKLIST.md`.
4. Update page `status`.
5. Update `wiki/index.md`, `coverage_matrix.md`, and `open_questions.md` if
   the promotion changes coverage or closes a question.
6. Append a log entry to `logs/log.md`.

## Demotion Rule

Demote a page from `stable` to `usable` or `draft` if a new source, code
change, example, or audit finds an unresolved contradiction or unsupported
claim.
