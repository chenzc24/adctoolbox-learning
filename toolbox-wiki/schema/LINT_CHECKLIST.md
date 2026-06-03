# Lint Checklist

Use this checklist for periodic health checks of `toolbox-wiki/`.

## Index And Logging

- [ ] Every generated wiki page is listed in `wiki/index.md`.
- [ ] Every ingest, query-to-page conversion, lint pass, or structural update has an entry in `logs/log.md`.
- [ ] `progress.md` still reflects the user's current learning state.
- [ ] `python tools/lint_wiki.py` passes.
- [ ] `schema/SEMANTIC_LINT_CHECKLIST.md` has been used for major ingests and before `stable` promotion.

## Source Discipline

- [ ] Every page has `source_links`.
- [ ] Every important claim identifies whether it is code-confirmed, example-verified, theory-supported, engineering-heuristic, or open-question.
- [ ] Raw sources under `raw/` have not been rewritten.
- [ ] Existing staged course files outside `toolbox-wiki/` have not been modified as part of wiki maintenance.

## Code Linkage

- [ ] Each source-code page links to at least one concept page.
- [ ] Each source-code page links to at least one workflow or rigor page when relevant.
- [ ] Each concept page links to the source-code pages where the concept appears.
- [ ] Key ADCToolbox functions have source-code pages:
  - [ ] `sar.py`
  - [ ] `compute_spectrum.py`
  - [ ] `fit_sine_4param.py`
  - [ ] `calibrate_weight_sine_lite.py`
  - [ ] `calibrate_weight_sine.py`
  - [ ] `_patch_rank_deficiency.py`

## Learning Path Linkage

- [ ] Pages that depend on prior ADC concepts link to staged ADC notes.
- [ ] Pages that depend on math link to staged math notes.
- [ ] Pages that depend on MATLAB parity link to staged MATLAB notes where useful.
- [ ] The staged path remains a readable route and has not been flattened into the wiki.

## Rigor

- [ ] Calibration pages state identifiability assumptions.
- [ ] Spectrum pages state window, side-bin, coherence, and noise-estimation assumptions.
- [ ] Redundant SAR pages distinguish radix/effective span from reachability, DNL/INL, and missing-code proof.
- [ ] Open questions have a suggested validation path.
- [ ] Mathematical rigor pages follow `schema/PROOF_PAGE_TEMPLATE.md`.
- [ ] Example notes follow `schema/EXAMPLE_NOTE_TEMPLATE.md`.

## Orphans And Duplication

- [ ] No generated wiki page is missing inbound links from `wiki/index.md` or related pages.
- [ ] Duplicate explanations are consolidated or cross-linked.
- [ ] Stale pages are marked and scheduled for update rather than silently contradicted.

## Automated Lint

Run from `toolbox-wiki/`:

```bash
python tools/lint_wiki.py
```

The script checks Markdown links, required metadata on generated wiki pages,
allowed status values, `wiki/index.md` coverage, log heading format, and raw
directory presence.

For keyword retrieval, run:

```bash
python tools/search_wiki.py calibration
python tools/search_wiki.py "rank deficiency" --raw
```
