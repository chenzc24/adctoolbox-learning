# Source Fidelity Audit: Sun Course Notes 2026-06-03

```yaml
scope: toolbox-wiki
status: draft
last_updated: 2026-06-03
```

## Verdict

The current Sun-course wiki source notes are still derived primarily from the
pre-extracted Markdown layer, but the high-priority ADC chapters have now been
cross-linked to the original course PDFs and spot-checked against extractable
PDF text.

This is a source-fidelity upgrade, not a full re-ingest. It confirms that the
existing Markdown distillation is aligned with the corresponding original PDF
chapters at the topic and keyword level, while leaving detailed slide-by-slide
verification as future work.

## Method

For each already-ingested Sun-course Markdown chapter:

1. Locate the matching original PDF under
   `raw/resources/ADCtoolbox/ADC基础/孙老师课件/`.
2. Extract PDF text with `pdftotext`.
3. Check that the PDF text is non-empty and matches the expected chapter theme.
4. Check a small set of chapter-specific keywords.
5. Add the original PDF to the corresponding source note `source_links`.
6. Add the rigor tag `primary-source-spot-checked`.

## Checked Chapter Map

| Wiki source note | Markdown source | Original PDF | PDF text chars | Keyword hits | Fidelity status |
| --- | --- | --- | ---: | ---: | --- |
| `wiki/source_notes/adc_metrics_ch3.md` | `03_ch3_ADC性能指标.md` | `ch3.pdf` | 21400 | 6/6 | matched |
| `wiki/source_notes/sampling_circuit_ch5.md` | `05_ch5_采样电路.md` | `ch5.pdf` | 38593 | 4/5 | matched |
| `wiki/source_notes/switched_cap_settling_noise_ch6.md` | `06_ch6_开关电容建立与噪声.md` | `ch6.pdf` | 14062 | 4/5 | matched |
| `wiki/source_notes/comparator_ch7.md` | `07_ch7_电压比较器.md` | `ch7.pdf` | 32424 | 4/5 | matched |
| `wiki/source_notes/flash_adc_ch8.md` | `08_ch8_Flash_ADC.md` | `ch8.pdf` | 11295 | 4/5 | matched |
| `wiki/source_notes/folding_interpolating_adc_ch9.md` | `09_ch9_Folding_Interpolating_ADC.md` | `ch9.pdf` | 6059 | 5/5 | matched |
| `wiki/source_notes/pipeline_adc_concept_ch10.md` | `10_ch10_Pipeline_ADC概念.md` | `ch10.pdf` | 14737 | 4/5 | matched |
| `wiki/source_notes/pipeline_adc_implementation_ch11.md` | `11_ch11_Pipeline_ADC实现.md` | `ch11.pdf` | 22537 | 5/5 | matched |
| `wiki/source_notes/sar_low_power_ch12a.md` | `12a_ch12_低功耗SAR_ADC.md` | `ch12 - low power.pdf` | 25736 | 5/5 | matched |
| `wiki/source_notes/high_speed_sar_ch12b.md` | `12b_ch12_高速SAR_ADC.md` | `ch12 - high speed.pdf` | 13790 | 5/5 | matched |
| `wiki/source_notes/time_interleaving_ch13.md` | `13_ch13_Time_Interleaving.md` | `ch13.pdf` | 9374 | 5/5 | matched |
| `wiki/source_notes/oversampling_adc_ch14.md` | `14_ch14_过采样ADC.md` | `ch14 Oversampling ADCs.pdf` | 24471 | 5/5 | matched |
| `wiki/source_notes/adc_fom_ch16.md` | `16_ch16_ADC_FOM.md` | `ch16 ADC Figures of Merit.pdf` | 26814 | 5/5 | matched |
| `wiki/source_notes/data_converter_testing_ch17.md` | `17_ch17_数据转换器测试.md` | `ch17 Data Converter Testing.pdf` | 25658 | 5/6 | matched with minor follow-up |

## Interpretation

The check supports the current use of the pre-extracted Markdown as a learning
and retrieval layer. The Markdown chapters appear to be faithful topic-level
summaries of the original PDFs for the chapters currently used by the wiki.

However, the check is not a proof that every formula, figure, assumption, or
engineering caveat in the PDFs was preserved. The source notes should therefore
remain `draft` until page-level review has happened.

## Minor Follow-Ups

- `ch17 Data Converter Testing.pdf` did not hit the `ENOB` keyword in this
  simple text check, although it did hit testing, DNL, INL, FFT, and histogram.
  Review the exact dynamic-metric slides manually before promoting related
  pages to `stable`.
- `ch10.pdf` matched Pipeline, residue, stage, and ADC, but not the `MDAC`
  keyword in this simple check. Treat MDAC-specific statements as anchored more
  strongly by `ch11.pdf` unless slide-level review confirms the term in ch10.
- Several PDFs use English terminology while Markdown notes use Chinese
  terminology. Keyword misses can therefore be terminology artifacts rather
  than real source mismatch.

## Still Not Fully Ingested

The following Sun-course Markdown/PDF pairs exist but are not yet part of the
core wiki source-note layer:

- `01_ch1_课程介绍与学习方法.md` / `ch1.pdf`
- `02_ch2_数据转换器高层图景.md` / `ch2.pdf`
- `04_ch4_Nyquist_DAC基础.md` / `ch4.pdf`
- `15_ch15_过采样DAC.md` / `ch15.pdf`

These are lower priority for the current ADCToolbox calibration path, but they
should be ingested if the wiki expands toward a full ADC/DAC course companion.

## Maintenance Rule Added By This Audit

For any future Sun-course source note:

1. Link both the pre-extracted Markdown and the original PDF in `source_links`.
2. Use `source-confirmed` only after the Markdown has been read.
3. Use `primary-source-spot-checked` only after the corresponding PDF has been
   text-extracted or manually inspected.
4. Use `primary-source-reviewed` only after slide-level formulas, figures, and
   assumptions have been checked.
5. Keep the page in `draft` unless the source note clearly states what was
   checked and what remains unverified.

## Next Upgrade

The next source-fidelity step is a chapter-by-chapter review page for the most
calibration-critical PDFs:

1. `ch12 - low power.pdf` and `ch12 - high speed.pdf` for SAR assumptions.
2. `ch17 Data Converter Testing.pdf` for metric definitions and test setup.
3. `ch10.pdf` and `ch11.pdf` for Pipeline residue and MDAC calibration hooks.
