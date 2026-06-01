"""Whole-workflow ADCToolbox demo for learning.

Run from the Python package directory:

    cd E:/ADCToolbox/python
    uv run python ../agent_playground/adctoolbox_learning/demos/whole_workflow_demo.py

Everything is saved under agent_playground/adctoolbox_learning/outputs/,
which is ignored by git.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import adctoolbox
from adctoolbox import (
    analyze_error_autocorr,
    analyze_error_pdf,
    analyze_spectrum,
    amplitudes_to_snr,
    calculate_jitter_limit,
    calculate_walden_fom,
    calibrate_weight_sine,
    deinterleave,
    find_coherent_frequency,
    fit_sine_4param,
    interleave,
    nsd_to_snr,
    predict_spurs,
    sar_apply_cap_mismatch,
    sar_convert,
    sar_ideal_weights,
    sar_reconstruct,
    snr_to_enob,
    snr_to_nsd,
)
from adctoolbox.dout import analyze_bit_activity, analyze_weight_radix
from adctoolbox.siggen import ADC_Signal_Generator


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "whole_workflow"

FS = 100e6
N = 2**13
FIN_TARGET = 6.1e6
ADC_BITS = 12
INPUT_AMPLITUDE = 0.49
INPUT_DC = 0.5
RNG_SEED = 20260530


def finite_float(value):
    """JSON-friendly float conversion."""
    value = float(value)
    if np.isfinite(value):
        return value
    return None


def spectrum_row(label: str, metrics: dict) -> dict:
    return {
        "case": label,
        "sndr_dbc": finite_float(metrics["sndr_dbc"]),
        "snr_dbc": finite_float(metrics["snr_dbc"]),
        "sfdr_dbc": finite_float(metrics["sfdr_dbc"]),
        "thd_dbc": finite_float(metrics["thd_dbc"]),
        "enob": finite_float(metrics["enob"]),
        "nsd_dbfs_hz": finite_float(metrics["nsd_dbfs_hz"]),
    }


def centered(signal: np.ndarray) -> np.ndarray:
    return np.asarray(signal, dtype=float) - np.mean(signal)


def run_spectrum(signal: np.ndarray, ax, title: str, fs: float = FS) -> dict:
    metrics = analyze_spectrum(
        signal,
        fs=fs,
        max_scale_range=(-0.5, 0.5),
        win_type="rectangular",
        side_bin=0,
        max_harmonic=5,
        nf_method=3,
        create_plot=True,
        show_label=True,
        ax=ax,
    )
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_ylim(-155, 5)
    return metrics


def step_1_generate_signal(fin: float) -> dict:
    """Generate clean and nonideal analog-output signals."""
    np.random.seed(RNG_SEED)
    gen = ADC_Signal_Generator(N=N, Fs=FS, Fin=fin, A=INPUT_AMPLITUDE, DC=INPUT_DC)

    clean = gen.get_clean_signal()
    distorted = gen.apply_static_nonlinearity_hd(clean, hd2_dB=-78, hd3_dB=-70)
    noisy = gen.apply_thermal_noise(distorted, noise_rms=70e-6)
    quantized = gen.apply_quantization_noise(noisy, n_bits=ADC_BITS, quant_range=(0.0, 1.0))

    return {
        "clean": clean,
        "distorted_noisy_quantized": quantized,
    }


def step_2_spectrum(signal_pack: dict) -> list[dict]:
    """Measure spectrum quality of clean and nonideal signals."""
    clean = centered(signal_pack["clean"])
    nonideal = centered(signal_pack["distorted_noisy_quantized"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    clean_metrics = run_spectrum(clean, axes[0], "Clean Coherent Sine")
    nonideal_metrics = run_spectrum(nonideal, axes[1], "Generated ADC Output")
    fig.savefig(OUTPUT_DIR / "01_spectrum_clean_vs_nonideal.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    return [
        spectrum_row("clean_sine", clean_metrics),
        spectrum_row("generated_adc_output", nonideal_metrics),
    ]


def step_3_analog_debug(nonideal_signal: np.ndarray, norm_freq: float) -> dict:
    """Fit the sine and inspect residual/error behavior."""
    signal = centered(nonideal_signal)
    fit = fit_sine_4param(signal, frequency_estimate=norm_freq)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    pdf = analyze_error_pdf(
        signal,
        resolution=ADC_BITS,
        full_scale=1.0,
        frequency=norm_freq,
        create_plot=True,
        ax=axes[0],
        title="Error PDF",
    )
    acf = analyze_error_autocorr(
        signal,
        frequency=norm_freq,
        max_lag=60,
        create_plot=True,
        ax=axes[1],
        title="Error Autocorrelation",
    )
    fig.savefig(OUTPUT_DIR / "02_analog_error_debug.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    return {
        "fit_frequency_norm": finite_float(fit["frequency"]),
        "fit_amplitude": finite_float(fit["amplitude"]),
        "fit_dc": finite_float(fit["dc_offset"]),
        "error_pdf_mu_lsb": finite_float(pdf["mu"]),
        "error_pdf_sigma_lsb": finite_float(pdf["sigma"]),
        "error_pdf_kl_divergence": finite_float(pdf["kl_divergence"]),
        "error_acf_lag0": finite_float(acf["acf"][np.where(acf["lags"] == 0)[0][0]]),
    }


def step_4_sar_and_calibration(fin_bin: int) -> tuple[list[dict], dict]:
    """Model a SAR ADC, then calibrate its bit weights from sine data."""
    rng = np.random.default_rng(RNG_SEED)
    n = np.arange(N)
    vin = INPUT_DC + INPUT_AMPLITUDE * np.sin(2.0 * np.pi * fin_bin * n / N)

    nominal_weights = sar_ideal_weights(ADC_BITS)
    actual_weights = sar_apply_cap_mismatch(nominal_weights, sigma=0.004, rng=rng)

    ideal_bits = sar_convert(vin, nominal_weights, quant_range=(0.0, 1.0))
    nonideal_bits = sar_convert(
        vin,
        actual_weights,
        quant_range=(0.0, 1.0),
        sampling_noise_rms=40e-6,
        comparator_noise_rms=40e-6,
        rng=rng,
    )

    ideal_aout = centered(sar_reconstruct(ideal_bits, nominal_weights, quant_range=(0.0, 1.0)))
    nominal_aout = centered(sar_reconstruct(nonideal_bits, nominal_weights, quant_range=(0.0, 1.0)))

    cal = calibrate_weight_sine(
        nonideal_bits,
        freq=fin_bin / N,
        harmonic_order=3,
        verbose=0,
    )
    calibrated_aout = centered(np.asarray(cal["calibrated_signal"], dtype=float))

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8), constrained_layout=True)
    ideal_metrics = run_spectrum(ideal_aout, axes[0], "Ideal SAR Output")
    nominal_metrics = run_spectrum(nominal_aout, axes[1], "Mismatch, Nominal Weights")
    calibrated_metrics = run_spectrum(calibrated_aout, axes[2], "After Sine Calibration")
    fig.savefig(OUTPUT_DIR / "03_sar_model_and_calibration.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    bit_activity = analyze_bit_activity(
        nonideal_bits,
        create_plot=True,
        ax=axes[0],
        title="SAR Bit Activity",
    )
    radix = analyze_weight_radix(
        cal["weight"],
        create_plot=True,
        ax=axes[1],
        title="Calibrated Weight Radix",
    )
    fig.savefig(OUTPUT_DIR / "04_digital_debug_bits_and_weights.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    np.savez_compressed(
        OUTPUT_DIR / "sar_model_data.npz",
        vin=vin,
        ideal_bits=ideal_bits,
        nonideal_bits=nonideal_bits,
        ideal_aout=ideal_aout,
        nominal_aout=nominal_aout,
        calibrated_aout=calibrated_aout,
        nominal_weights=nominal_weights,
        actual_weights=actual_weights,
        calibrated_weights=cal["weight"],
    )

    rows = [
        spectrum_row("sar_ideal", ideal_metrics),
        spectrum_row("sar_mismatch_nominal_weights", nominal_metrics),
        spectrum_row("sar_after_sine_calibration", calibrated_metrics),
    ]
    digital_summary = {
        "bit_activity_percent": [finite_float(x) for x in bit_activity],
        "weight_effres_bits": finite_float(radix["effres"]),
        "refined_calibration_frequency": finite_float(cal["refined_frequency"]),
    }
    return rows, digital_summary


def step_5_time_interleave_and_conversions(fin: float, norm_freq: float) -> dict:
    """Demonstrate utility workflows beyond the main SAR path."""
    x = np.arange(24)
    channels = deinterleave(x, M=4)
    roundtrip = interleave(channels)

    ti_params = {
        "gain": np.array([1.000, 1.006, 0.995, 1.002]),
        "offset": np.array([0.0, 0.0015, -0.0010, 0.0005]),
        "skew": np.array([0.0, 0.8e-12, -0.6e-12, 0.3e-12]),
        "A": INPUT_AMPLITUDE,
        "fin": fin,
    }
    spurs = predict_spurs(ti_params, fs=FS, fin=fin, full_scale=0.5)
    strongest_spur = min(spurs, key=lambda row: row["dbc"])

    theoretical_snr = amplitudes_to_snr(INPUT_AMPLITUDE, 70e-6)
    nsd = snr_to_nsd(theoretical_snr, fs=FS, psignal_dbfs=0, osr=1)
    snr_back = nsd_to_snr(nsd, fs=FS, psignal_dbfs=0, osr=1)
    jitter_snr = calculate_jitter_limit(fin, 1e-12)
    walden = calculate_walden_fom(power=10e-3, fs=FS, enob=11.5)

    return {
        "deinterleave_shape": list(channels.shape),
        "interleave_roundtrip_ok": bool(np.array_equal(x, roundtrip)),
        "strongest_ti_spur_freq_hz": finite_float(strongest_spur["freq_hz"]),
        "strongest_ti_spur_dbc": finite_float(strongest_spur["dbc"]),
        "theoretical_snr_db": finite_float(theoretical_snr),
        "theoretical_enob_bits": finite_float(snr_to_enob(theoretical_snr)),
        "nsd_dbfs_hz": finite_float(nsd),
        "snr_recovered_from_nsd_db": finite_float(snr_back),
        "jitter_limited_snr_db_at_1ps": finite_float(jitter_snr),
        "walden_fom_j_per_step": finite_float(walden),
        "input_norm_frequency": finite_float(norm_freq),
    }


def write_summary(summary: dict) -> None:
    with open(OUTPUT_DIR / "workflow_summary.json", "w", encoding="ascii") as f:
        json.dump(summary, f, indent=2)

    spectrum_rows = summary["spectrum_rows"]
    with open(OUTPUT_DIR / "spectrum_metrics.csv", "w", encoding="ascii") as f:
        f.write("case,sndr_dbc,snr_dbc,sfdr_dbc,thd_dbc,enob,nsd_dbfs_hz\n")
        for row in spectrum_rows:
            f.write(
                f"{row['case']},{row['sndr_dbc']},{row['snr_dbc']},"
                f"{row['sfdr_dbc']},{row['thd_dbc']},{row['enob']},"
                f"{row['nsd_dbfs_hz']}\n"
            )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    fin, fin_bin = find_coherent_frequency(FS, FIN_TARGET, N)
    norm_freq = fin / FS

    print("ADCToolbox whole-workflow demo")
    print(f"Package version: {adctoolbox.__version__}")
    print(f"Coherent tone: Fin={fin / 1e6:.6f} MHz, bin={fin_bin}, N={N}")
    print()

    signal_pack = step_1_generate_signal(fin)
    spectrum_rows = step_2_spectrum(signal_pack)
    analog_debug = step_3_analog_debug(signal_pack["distorted_noisy_quantized"], norm_freq)
    sar_rows, digital_summary = step_4_sar_and_calibration(fin_bin)
    utilities_summary = step_5_time_interleave_and_conversions(fin, norm_freq)

    spectrum_rows.extend(sar_rows)
    summary = {
        "adctoolbox_version": adctoolbox.__version__,
        "fs_hz": FS,
        "n_samples": N,
        "fin_hz": fin,
        "fin_bin": fin_bin,
        "spectrum_rows": spectrum_rows,
        "analog_debug": analog_debug,
        "digital_debug": digital_summary,
        "time_interleave_and_conversions": utilities_summary,
    }
    write_summary(summary)

    print("Key spectrum results")
    for row in spectrum_rows:
        print(
            f"  {row['case']:<30} "
            f"SNDR={row['sndr_dbc']:>8.2f} dB  "
            f"ENOB={row['enob']:>6.2f} bits  "
            f"SFDR={row['sfdr_dbc']:>8.2f} dB"
        )

    print()
    print("Analog debug")
    print(
        f"  error sigma = {analog_debug['error_pdf_sigma_lsb']:.3f} LSB, "
        f"KL divergence = {analog_debug['error_pdf_kl_divergence']:.4f}"
    )

    print()
    print("Digital/SAR debug")
    print(f"  calibrated weight-list effective resolution = {digital_summary['weight_effres_bits']:.2f} bits")
    print(f"  first four bit activities = {digital_summary['bit_activity_percent'][:4]}")

    print()
    print("Other utilities")
    print(f"  deinterleave/interleave roundtrip OK = {utilities_summary['interleave_roundtrip_ok']}")
    print(
        "  strongest predicted TI spur = "
        f"{utilities_summary['strongest_ti_spur_freq_hz'] / 1e6:.3f} MHz, "
        f"{utilities_summary['strongest_ti_spur_dbc']:.2f} dBc"
    )

    print()
    print(f"Outputs saved under: {OUTPUT_DIR}")
    print("Read agent_playground/adctoolbox_learning/guides/whole_workflow_guide.md for the novice walkthrough.")


if __name__ == "__main__":
    main()
