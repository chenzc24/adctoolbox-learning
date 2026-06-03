# Semantic Lint Checklist

Automated lint catches bookkeeping failures. Semantic lint checks whether the
wiki still makes conceptual sense.

Run semantic lint periodically, after major ingests, and before promoting pages
to `stable`.

## Search And Scope

- [ ] Read `index.md`, `wiki/index.md`, `coverage_matrix.md`, and
  `open_questions.md` first.
- [ ] Search the wiki with `python tools/search_wiki.py <topic>`.
- [ ] Search source code or raw sources only when the wiki is insufficient.

## Link Health Beyond Syntax

- [ ] Each generated page has at least one meaningful inbound path from
  `wiki/index.md` or a related page.
- [ ] Each source-code page links to a concept page and a rigor/workflow page
  when relevant.
- [ ] Each concept page links to concrete code, raw source notes, or workflows.
- [ ] Source notes are integrated into concept/code/workflow/rigor pages rather
  than sitting as dead summaries.

## Semantic Islands

- [ ] No important topic appears only in one isolated page.
- [ ] Similar explanations are cross-linked or consolidated.
- [ ] Related pages agree on terminology.
- [ ] Acronyms and metrics have a single preferred definition page.

## Contradictions

- [ ] Check whether newer pages contradict older pages.
- [ ] Check whether code-confirmed statements disagree with raw notes.
- [ ] Check whether examples demonstrate less than the page claims.
- [ ] Record unresolved contradictions in `open_questions.md`.

## Staleness

- [ ] Pages that mention current project behavior still match the current code.
- [ ] Pages that mention planned gaps still match `coverage_matrix.md`.
- [ ] Health audits do not contain stale claims that were later fixed.
- [ ] Log entries describe the actual maintenance history.

## Rigor

- [ ] Calibration pages state identifiability assumptions.
- [ ] Spectrum pages state FFT/window/bin/noise assumptions.
- [ ] Example notes distinguish demonstration from proof.
- [ ] Rigor pages state proof obligations and validation recipes.
- [ ] Every `stable` page has "what this does not prove" or equivalent caveats.

## Output

Create or update an audit file under `audits/`, using:

```text
audits/semantic_lint_YYYY-MM-DD.md
```

The audit should list:

- pages checked;
- contradictions found;
- stale claims found;
- semantic islands found;
- promotions or demotions recommended;
- follow-up items added to `open_questions.md`.
