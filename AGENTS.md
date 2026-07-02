# adctoolbox-learning Agent Notes

This repository is a learning sub-repository for ADCToolbox. Treat it as a
course notebook, not as ordinary source documentation.

## Interaction and Edit Boundary

- Chat is primarily for learning, derivation, questioning, and clarification.
- Do not edit files just because a concept was discussed.
- Edit files only when the user explicitly asks to update, modify, move,
  supplement, reorganize, or write content into the repository.
- When the user asks a conceptual question, answer in chat first. If a document
  update seems useful, suggest it instead of silently changing files.
- When the user asks to update, preserve the learning path that led to the
  update. Do not replace it with a generic textbook summary.

## Notes vs Staged Course

`learner/notes.md` is a short-form review and indexing notebook.

Use it for:

- Core logic chains.
- Key formulas.
- Short definitions.
- Common misunderstandings.
- Pointers to the next stage.
- Compact summaries of what has already been learned.

Avoid using it for:

- Long derivations.
- Full mathematical proofs.
- Repeating large parts of staged course text.
- Detailed code walkthroughs.

`staged_course/stage_xx_*/stage_xx_*.md` is the detailed learning body.

Use it for:

- Rigorous explanations.
- Step-by-step mathematical derivations.
- Ground-up teaching of missing prerequisites.
- Examples and counterexamples.
- Connections to ADCToolbox implementation details.
- Explicit correction of earlier misunderstandings.

The normal pattern is:

```text
Detailed version -> staged_course
Compact version  -> learner/notes.md
```

If `notes.md` becomes bulky, reorganize and deduplicate it without losing the
core information.

## Corner and Optimization Log

`learner/corner-cases-and-optimization.md` records corner cases, subtle implementation
boundaries, documentation correction points, and possible optimization ideas.

Use it only when the maintainer explicitly asks to add or record an item there.
An Agent may suggest adding an item, but must not silently promote ordinary
discussion into this log.

Each entry must include:

- Date.
- Code location.
- Problem statement.
- Principle derivation.

Preserve the context that made the corner important. If later code or course
content resolves the issue, append a status/update note under the existing
entry instead of deleting the historical record.

## Controversial Questions Log

`learner/controversial-questions.md` records unresolved or partially resolved
learning debates. Use it for questions where the learner has found a real
boundary between a simplified explanation and a more rigorous interpretation.

This file is different from `learner/notes.md`:

- `notes.md` keeps compact review knowledge.
- `controversial-questions.md` keeps the shape of a debate, including why the
  issue was confusing, what is currently believed, and what remains open.

Use this log for topics such as:

- Whether a common correction really recovers a physical truth.
- Whether a metric is a true quantity or an estimator under test conditions.
- Whether a textbook statement hides assumptions that matter for ADCToolbox.
- Whether code behavior matches the theoretical interpretation.
- Which standards, experiments, or later stages should be used to verify the
  current understanding.

Do not treat entries as final doctrine. Each entry should clearly distinguish:

- The question.
- The trigger or learner objection.
- The current working consensus.
- The remaining boundary or uncertainty.
- The impact on course wording or code interpretation.
- Follow-up experiments, standards, or later-stage links.

When a controversy is later resolved, append an update under the existing entry
instead of deleting the discussion. Preserve the reasoning history because it is
part of the learning material.

## Stage Continuity

Stages are connected parts of one learning path. Do not treat them as isolated
articles.

Current learning chain:

```text
Stage 00 / Stage 01:
    ADC basics, sampling, full-scale, quantization foundations

Stage 02:
    DFT / FFT, coherent sampling, windowing, leakage, SNR, SNDR,
    THD, SFDR, ENOB, NSD, OSR
    Purpose: use spectrum metrics to form first-level diagnostic hypotheses

Stage 03:
    sine fitting, residual/error, PDF, autocorrelation, error spectrum,
    error by value, error by phase
    Purpose: verify Stage 02 hypotheses through residual structure

Stage 04:
    connect residual and spectrum symptoms to concrete ADC non-idealities

Stage 06:
    deterministic error, calibration, and why random noise cannot be simply
    calibrated away
```

When moving or adding a concept, decide placement by its role in the learning
chain, not just by the name of the topic.

## User Understanding Comes First

- The user's original reasoning is part of the course material.
- When the user has already developed a partial model, use that model as the
  starting point.
- Preserve the user's question-driven logic where it helps learning.
- Correct inaccuracies carefully, and explain why the correction is needed.
- Prefer "your intuition is close, but the missing distinction is..." over
  replacing the discussion with a detached final answer.

## Theory and Code Must Meet

When staged course content explains ADCToolbox behavior, connect the theory to
actual functions, variables, or implementation choices where practical.

Examples from Stage 02:

```text
win_type
side_bin
window_gain
equiv_noise_bw_factor
power_correction
sig_peak
sig_linear
n_inband
rfft_inband_bin_count
```

If the current code behavior differs from a common textbook expectation, the
course should say so explicitly and use the code as the reference for this
repository.

## Style

- Write primarily in Chinese for learner-facing course content.
- Use English technical terms when they are the natural ADC/DSP terms, such as
  `coherent sampling`, `window`, `residual`, `spur`, `noise floor`, `ENBW`.
- Prefer tight logic chains over decorative prose.
- Use equations when they clarify a claim.
- Add code references when they prevent ambiguity.
- Keep `notes.md` concise and scannable.
- Let staged course sections be longer when the user needs first-principles
  derivations.

## Commit Practice

- Commit inside this sub-repository when the user asks for a sub-repo commit.
- After committing in the sub-repository, remember that the parent repository
  will show the submodule pointer as modified.
