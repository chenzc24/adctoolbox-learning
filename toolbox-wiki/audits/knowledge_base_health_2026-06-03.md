# Knowledge Base Health Audit 2026-06-03

```yaml
scope: toolbox-wiki
raw_resource_location: raw/resources
protected_scope: existing adctoolbox-learning content outside toolbox-wiki
status: baseline-audit
last_updated: 2026-06-03
```

## Short Conclusion

The knowledge base is now structurally usable, but still in the seed stage.
It has a safe sidecar structure, imported raw resources, a maintenance rule
set, and the first code-linked pages for SAR modeling and weight calibration.
It is not yet complete enough to serve as a mature full LLM Wiki because
example-level validation, deeper mathematical proof pages, broader raw-source
ingestion, and richer cross-linking are still incomplete.

## Completeness

Current level: medium-low.

What is already covered:

- Raw learning resources have been moved under `toolbox-wiki/raw/resources`.
- The first reusable topic page exists for ADC weight calibration.
- The first source-code pages exist for SAR modeling and sine-weight
  calibration.
- One end-to-end workflow exists from SAR modeling to calibration.
- One rigor page records the major mathematical and engineering gaps.

Main missing areas:

- Spectrum validation workflow: before/after calibration comparisons still
  need a dedicated workflow page.
- Sine fitting rigor: convergence, estimator variance, and bias under harmonic
  distortion still need deeper treatment.
- Rank-deficiency rigor: redundant SAR reachability, effective weights,
  physical-weight observability, and missing-code behavior still need deeper
  proof pages.
- Example path: examples under `python/src/adctoolbox/examples/05_debug_digital`
  and `02_spectrum` need example notes.
- Raw-source path: the first Markdown source notes exist, but the PDF and DOCX
  sources are not yet systematically summarized into source notes.

## Code Relevance

Current level: medium.

Strengths:

- The current pages link directly to core source files in `python/src/adctoolbox`.
- The page set follows the real calibration chain:
  `sar_convert` -> bit matrix -> `calibrate_weight_sine*` -> reconstructed
  waveform -> spectrum validation.
- The rigor page is tied to implementation risks instead of being a generic
  math essay.

Weak points:

- Some pages still explain at module level rather than line-level algorithm
  blocks.
- There are now pages for `compute_spectrum.py`, `fit_sine_4param.py`, and
  `_patch_rank_deficiency.py`, which closes the first major code-linkage gap.
- The examples have not yet been mapped into "what this proves" and "what it
  does not prove".
- The coverage matrix exists, but it still needs more rows and example-level
  coverage.

## Maintenance Rule Maturity

Current level: medium.

Strengths:

- `schema/WIKI_RULES.md` defines source discipline, confidence levels,
  page requirements, and calibration/metric rigor requirements.
- `schema/LINT_CHECKLIST.md` gives a repeatable audit path.
- `logs/log.md` now records structural and content updates.
- `progress.md` protects the existing staged learning path and lists next
  pages.
- `coverage_matrix.md` tracks topic coverage across concepts, source code,
  workflows, rigor, and source notes.
- `open_questions.md` keeps unresolved mathematical and engineering questions
  visible.

Weak points:

- `tools/lint_wiki.py` now verifies Markdown links, required metadata,
  `wiki/index.md` coverage, log heading format, and raw directory presence.
- There is no rule yet for when a draft page can be promoted to stable.

## Mathematical Rigor Status

Current level: early.

Most important gaps:

- Identifiability: no formal condition yet for when the bit matrix and sine
  basis uniquely determine ADC weights.
- Conditioning: no requirement yet to report condition number, rank, singular
  values, or weight uncertainty.
- Frequency coupling: no derivation yet for how frequency error biases the
  solved weights.
- Redundant SAR: no proof yet that nominal radix, effective span, DNL/INL, and
  missing-code behavior are all acceptable.
- Validation: no required train/test split, amplitude sweep, frequency sweep,
  mismatch Monte Carlo, or corner-style verification checklist.
- Attribution: harmonic rejection can improve residuals while making it harder
  to distinguish weight error, source distortion, and static nonlinearity.

## Recommended Next Improvement Pass

1. Add `wiki/workflows/spectrum_validation_before_after_calibration.md`.
2. Add `wiki/rigor/spectrum_metric_statistical_risks.md`.
3. Add `wiki/rigor/redundant_sar_reachability.md`.
4. Add `wiki/concepts/rank_deficiency.md`.
5. Add `wiki/concepts/least_squares_adc_calibration.md`.
6. Add example notes for the key digital calibration and spectrum examples.
7. Add a promotion checklist for moving pages from `draft` to `stable`.

## Verdict

The current wiki is safe to continue using as a sidecar learning knowledge
base. It does not damage the stage-based route, and it now has automated
bookkeeping lint. It is still not a mature full LLM Wiki. The right next move
is to expand example-level validation, redundant SAR rigor, spectrum metric
statistics, and page-stability rules while keeping all edits inside
`toolbox-wiki/`.
