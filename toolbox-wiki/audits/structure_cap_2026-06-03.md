# Structure Cap Audit 2026-06-03

```yaml
scope: toolbox-wiki
status: structure-capped
last_updated: 2026-06-03
```

## Verdict

The structural layer is capped for the current scale of the ADCToolbox learner
wiki.

The wiki now has:

- a readable entry structure;
- a content catalog;
- a coverage matrix;
- an open-question queue;
- raw/source/wiki/schema/log/audit/tool separation;
- automated bookkeeping lint;
- dependency-free keyword search;
- page promotion rules;
- semantic lint rules;
- proof-page and example-note templates.

## Retrieval Structure

Primary navigation:

- `index.md`
- `wiki/index.md`
- `coverage_matrix.md`
- `open_questions.md`

Search:

```bash
python tools/search_wiki.py calibration
python tools/search_wiki.py "rank deficiency" --raw
```

## Maintenance Structure

Automated lint:

```bash
python tools/lint_wiki.py
```

Manual semantic lint:

- `schema/SEMANTIC_LINT_CHECKLIST.md`

Page promotion:

- `schema/PROMOTION_RULES.md`

Templates:

- `schema/PAGE_TEMPLATE.md`
- `schema/PROOF_PAGE_TEMPLATE.md`
- `schema/EXAMPLE_NOTE_TEMPLATE.md`

## What Is Now Structural Versus Content

Solved structurally:

- Retrieval route.
- Document taxonomy.
- Raw-source protection.
- Page metadata.
- Index and log rules.
- Automated bookkeeping lint.
- Semantic lint checklist.
- Page promotion lifecycle.
- Proof-page format.
- Example-note format.

Still content work:

- Ingesting examples.
- Writing mathematical proof pages.
- Promoting individual pages to `usable` or `stable`.
- Expanding raw PDF/DOCX source notes.
- Adding deeper cross-links as the page count grows.

## Verification

Automated lint passed:

```text
toolbox-wiki lint passed
```

Search smoke tests returned focused results for:

- `rank deficiency`
- `calibration`

## Structural Cap Rule

Do not add more top-level structure unless a real scaling problem appears.
Future work should normally add content within the existing categories, update
the matrix/log/questions, and run lint.
