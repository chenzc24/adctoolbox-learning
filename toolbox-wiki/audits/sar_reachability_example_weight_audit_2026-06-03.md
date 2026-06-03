# SAR Reachability Example Weight Audit

```yaml
scope: toolbox-wiki
source_links:
  - ../tools/audit_sar_reachability.py
  - ../../../../python/src/adctoolbox/models/sar.py
  - ../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d03_redundancy_comparison.py
  - ../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d16_sar_unit_cap_mismatch_mc.py
  - ../../../../python/src/adctoolbox/examples/05_debug_digital/exp_d18_sar_redundant_mismatch_training_length_sweep.py
related_pages:
  - ../wiki/rigor/redundant_sar_reachability.md
  - ../wiki/source_notes/examples/exp_d03_redundancy_comparison.md
  - ../wiki/source_notes/examples/exp_d16_sar_unit_cap_mismatch_mc.md
  - ../wiki/source_notes/examples/exp_d18_sar_redundant_mismatch_training_length_sweep.md
status: active
last_updated: 2026-06-03
```

This audit applies `tools/audit_sar_reachability.py` to the SAR weight lists
that currently anchor the wiki's redundancy examples.

## Method

The audit records a conservative interval margin:

```text
margin[j] = sum(weights[j+1:]) - weights[j]
```

Positive margin at bit `j` means the remaining lower-weight decisions have
enough nominal span to cover an error in that branch. Negative margin means
that bit has no local redundancy under this simple one-sided interval test.

The script also enumerates static code sums for lists up to 24 weights and
reports duplicate code sums. Duplicate sums are expected for deliberately
redundant arrays, but they are not by themselves a proof of calibrated
performance.

## Audited Cases

| case | bits | min_margin | first_negative_bit | duplicate_codes | code_step_min | code_step_max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `exp_d03_binary_nominal` | 12 | -0.000244140625 | 0 | 0 | 0.000244140625 | 0.000244140625 |
| `exp_d03_binary_msb_minus_2pct` | 12 | -0.000246606692 | 1 | 0 | 0.00000986426768 | 0.000246606692 |
| `exp_d03_binary_msb_plus_2pct` | 12 | -0.0101427135 | 0 | 0 | 0.000241723391 | 0.0101427135 |
| `exp_d03_redundant_nominal` | 13 | -0.000217013889 | 3 | 3584 | 0.000217013889 | 0.000217013889 |
| `exp_d03_redundant_msb_minus_2pct` | 13 | -0.000218960202 | 3 | 3072 | 0.00000875840807 | 0.000218960202 |
| `exp_d03_redundant_msb_plus_2pct` | 13 | -0.000215101872 | 3 | 3072 | 0.00000860407489 | 0.000215101872 |
| `exp_d16_d18_radix18_nominal` | 18 | -0.0000152587891 | 14 | 196608 | 0.0000152587891 | 0.0000152587891 |

## Interpretation

### D03 Strict Binary

The nominal strict-binary list has negative branch margin from the MSB onward.
That matches the textbook idea that radix-2 search has no local correction
range: once a high-bit decision is wrong, lower bits cannot fully repair it.

With `+2%` MSB mismatch, the first margin becomes much more negative. This is
the hard direction for strict binary in the D03 example because the MSB step is
too large for the lower array to cover.

With `-2%` MSB mismatch, the first margin becomes positive, but lower bits
remain non-redundant. This explains why one mismatch sign can look less severe
without implying a general redundant architecture.

### D03 Duplicate-Bit Redundancy

The redundant D03 list duplicates the `256` capacitor. Its first three branch
margins are positive, so the top part of the search has a real local correction
range under this interval test.

The lower tail is still binary-like and has negative margins. Therefore the
example supports a more careful claim:

```text
D03 demonstrates high-bit redundancy, not all-bit redundancy.
```

The duplicate-code count is nonzero, as expected for a redundant weighted-sum
representation.

### D16/D18 Radix Approximately 1.8

The radix-approximately-1.8 list has positive margins through bit 13 and
negative margins only in the final tail. This is closer to a distributed
redundancy design than the D03 single duplicated-bit case.

The audit result supports using D16 and D18 as the stronger example pair for
redundant SAR calibration studies. It does not prove calibration success by
itself; the calibration claim still requires excitation, conditioning, solver
diagnostics, and independent validation captures.

## Remaining Gap

This page is a stored manual audit. The next maintenance step is to regenerate
it automatically from the example source files or from a small machine-readable
weight-list manifest, then fail lint if the stored values drift from code.
