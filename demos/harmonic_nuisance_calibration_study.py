"""Study how harmonic nuisance terms affect sine-based SAR weight calibration.

Run from the Python package directory:

    cd E:/ADCToolbox/python
    uv run python ../learning/adctoolbox-learning/demos/harmonic_nuisance_calibration_study.py

Outputs are written under:

    learning/adctoolbox-learning/outputs/harmonic_nuisance_calibration_study/
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from adctoolbox import (
    analyze_spectrum,
    calibrate_weight_sine,
    find_coherent_frequency,
    sar_apply_cap_mismatch,
    sar_convert,
    sar_ideal_weights,
)


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "harmonic_nuisance_calibration_study"

FS = 100e6
N = 2**13
ADC_BITS = 12
INPUT_DC = 0.5
INPUT_AMPLITUDE = 0.49
SAMPLING_NOISE_RMS = 40e-6
COMPARATOR_NOISE_RMS = 40e-6
MC_RUNS = 32


def centered(signal: np.ndarray) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    return signal - np.mean(signal)


def sine_input(bin_idx: int, amplitude: float = INPUT_AMPLITUDE, h3_dbc: float | None = None) -> np.ndarray:
    n = np.arange(N)
    signal = INPUT_DC + amplitude * np.sin(2.0 * np.pi * bin_idx * n / N)
    if h3_dbc is not None:
        signal += amplitude * 10.0 ** (h3_dbc / 20.0) * np.sin(
            2.0 * np.pi * 3 * bin_idx * n / N + 0.7
        )
    return signal


def spectrum(signal: np.ndarray) -> dict:
    return analyze_spectrum(
        centered(signal),
        fs=FS,
        max_scale_range=(-0.5, 0.5),
        win_type="rectangular",
        side_bin=0,
        max_harmonic=5,
        nf_method=3,
        create_plot=False,
        show_label=False,
    )


def metric_row(metrics: dict) -> dict:
    return {
        "enob": float(metrics["enob"]),
        "sndr_dbc": float(metrics["sndr_dbc"]),
        "sfdr_dbc": float(metrics["sfdr_dbc"]),
        "thd_dbc": float(metrics["thd_dbc"]),
        "snr_dbc": float(metrics["snr_dbc"]),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def quantiles(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
    }


def orthonormal_columns(matrix: np.ndarray) -> np.ndarray:
    q, r = np.linalg.qr(np.asarray(matrix, dtype=float))
    keep = np.abs(np.diag(r)) > 1e-10
    return q[:, keep]


def remove_subspace(q: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return matrix - q @ (q.T @ matrix)


def harmonic_basis(bin_idx: int, orders: list[int]) -> np.ndarray:
    n = np.arange(N)
    cols = []
    for order in orders:
        cols.append(np.cos(2.0 * np.pi * order * bin_idx * n / N))
        cols.append(np.sin(2.0 * np.pi * order * bin_idx * n / N))
    return np.column_stack(cols)


def top_projected_weight_direction(bits: np.ndarray, bin_idx: int, orders: list[int]) -> tuple[float, np.ndarray]:
    """Find the weight-error direction whose code error most overlaps a harmonic subspace."""
    n = np.arange(N)
    fundamental = np.column_stack(
        [
            np.ones(N),
            np.cos(2.0 * np.pi * bin_idx * n / N),
            np.sin(2.0 * np.pi * bin_idx * n / N),
        ]
    )
    q_fund = orthonormal_columns(fundamental)
    bit_residual = remove_subspace(q_fund, bits.astype(float))
    harm_residual = remove_subspace(q_fund, harmonic_basis(bin_idx, orders))
    q_harm = orthonormal_columns(harm_residual)

    u, s, vt = np.linalg.svd(bit_residual, full_matrices=False)
    keep = s > s[0] * 1e-10
    u_keep = u[:, keep]
    s_keep = s[keep]
    v_keep = vt[keep, :].T

    overlap = u_keep.T @ q_harm @ q_harm.T @ u_keep
    eigenvalues, eigenvectors = np.linalg.eigh(overlap)
    idx = int(np.argmax(eigenvalues))
    left_combination = eigenvectors[:, idx]
    weight_direction = v_keep @ (left_combination / s_keep)
    weight_direction /= np.linalg.norm(weight_direction)
    return float(eigenvalues[idx]), weight_direction


def projection_fraction(signal: np.ndarray, bin_idx: int, orders: list[int]) -> float:
    n = np.arange(N)
    fundamental = np.column_stack(
        [
            np.ones(N),
            np.cos(2.0 * np.pi * bin_idx * n / N),
            np.sin(2.0 * np.pi * bin_idx * n / N),
        ]
    )
    q_fund = orthonormal_columns(fundamental)
    residual = remove_subspace(q_fund, signal.reshape(-1, 1)).ravel()
    harm_residual = remove_subspace(q_fund, harmonic_basis(bin_idx, orders))
    q_harm = orthonormal_columns(harm_residual)
    projected = q_harm @ (q_harm.T @ residual)
    return float(np.sum(projected * projected) / np.sum(residual * residual))


def calibrate_and_evaluate(
    train_bits: np.ndarray,
    val_bits: np.ndarray,
    actual_weights: np.ndarray,
    train_bin: int,
    harmonic_order: int,
) -> dict:
    cal = calibrate_weight_sine(
        train_bits,
        freq=train_bin / N,
        harmonic_order=harmonic_order,
        verbose=0,
    )
    weights = np.asarray(cal["weight"], dtype=float)
    metrics = metric_row(spectrum(val_bits.astype(float) @ weights))
    actual_norm = actual_weights / np.sum(actual_weights)
    weights_norm = weights / np.sum(weights)
    metrics["weight_shape_error"] = float(
        np.linalg.norm(weights_norm - actual_norm) / np.linalg.norm(actual_norm)
    )
    return metrics


def experiment_random_mismatch(train_bin: int, val_bin: int, nominal_weights: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    sigmas = [0.004, 0.01, 0.02, 0.05]
    harmonic_orders = [1, 3, 7, 15, 31]

    for sigma in sigmas:
        for seed in range(MC_RUNS):
            actual = sar_apply_cap_mismatch(
                nominal_weights,
                sigma=sigma,
                rng=np.random.default_rng(1000 + seed),
            )
            train_bits = sar_convert(
                sine_input(train_bin),
                actual,
                quant_range=(0.0, 1.0),
                sampling_noise_rms=SAMPLING_NOISE_RMS,
                comparator_noise_rms=COMPARATOR_NOISE_RMS,
                rng=np.random.default_rng(2000 + seed),
            )
            val_bits = sar_convert(
                sine_input(val_bin),
                actual,
                quant_range=(0.0, 1.0),
                sampling_noise_rms=SAMPLING_NOISE_RMS,
                comparator_noise_rms=COMPARATOR_NOISE_RMS,
                rng=np.random.default_rng(3000 + seed),
            )
            nominal_metrics = metric_row(spectrum(val_bits.astype(float) @ nominal_weights))
            rows.append(
                {
                    "experiment": "random_mismatch",
                    "sigma": sigma,
                    "seed": seed,
                    "case": "nominal_weights",
                    "harmonic_order": 0,
                    **nominal_metrics,
                    "weight_shape_error": "",
                }
            )

            for harmonic_order in harmonic_orders:
                metrics = calibrate_and_evaluate(
                    train_bits,
                    val_bits,
                    actual,
                    train_bin,
                    harmonic_order,
                )
                rows.append(
                    {
                        "experiment": "random_mismatch",
                        "sigma": sigma,
                        "seed": seed,
                        "case": "calibrated",
                        "harmonic_order": harmonic_order,
                        **metrics,
                    }
                )
    return rows


def experiment_adversarial_projection(train_bin: int, val_bin: int, nominal_weights: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    amplitude = 0.30
    nominal_bits = sar_convert(sine_input(train_bin, amplitude=amplitude), nominal_weights, quant_range=(0.0, 1.0))
    harmonic_sets = {
        "H2_H3": [2, 3],
        "H2_to_H7": list(range(2, 8)),
        "H2_to_H15": list(range(2, 16)),
        "H2_to_H31": list(range(2, 32)),
    }
    harmonic_orders = [1, 3, 7, 15, 31]
    relative_norm = 1e-2

    for label, orders in harmonic_sets.items():
        top_fraction, direction = top_projected_weight_direction(nominal_bits, train_bin, orders)
        if np.sum(direction * nominal_weights) < 0:
            direction = -direction

        delta = relative_norm * np.linalg.norm(nominal_weights) * direction
        actual = nominal_weights + delta
        if np.any(actual <= 0):
            continue

        train_bits = sar_convert(sine_input(train_bin, amplitude=amplitude), actual, quant_range=(0.0, 1.0))
        val_bits = sar_convert(sine_input(val_bin, amplitude=amplitude), actual, quant_range=(0.0, 1.0))
        mismatch_error = train_bits.astype(float) @ (nominal_weights - actual)
        actual_projection = projection_fraction(mismatch_error, train_bin, orders)

        nominal_metrics = metric_row(spectrum(val_bits.astype(float) @ nominal_weights))
        rows.append(
            {
                "experiment": "adversarial_projection",
                "harmonic_set": label,
                "top_fixed_bit_projection": top_fraction,
                "actual_projection": actual_projection,
                "case": "nominal_weights",
                "harmonic_order": 0,
                **nominal_metrics,
                "weight_shape_error": "",
            }
        )

        for harmonic_order in harmonic_orders:
            metrics = calibrate_and_evaluate(
                train_bits,
                val_bits,
                actual,
                train_bin,
                harmonic_order,
            )
            rows.append(
                {
                    "experiment": "adversarial_projection",
                    "harmonic_set": label,
                    "top_fixed_bit_projection": top_fraction,
                    "actual_projection": actual_projection,
                    "case": "calibrated",
                    "harmonic_order": harmonic_order,
                    **metrics,
                }
            )
    return rows


def experiment_external_h3(train_bin: int, val_bin: int, nominal_weights: np.ndarray) -> list[dict]:
    rows: list[dict] = []
    harmonic_orders = [1, 3, 7]
    h3_levels = [None, -80, -70, -60, -50, -40]
    sigma = 0.01

    for h3_level in h3_levels:
        for seed in range(MC_RUNS):
            actual = sar_apply_cap_mismatch(
                nominal_weights,
                sigma=sigma,
                rng=np.random.default_rng(5000 + seed),
            )
            train_bits = sar_convert(
                sine_input(train_bin, h3_dbc=h3_level),
                actual,
                quant_range=(0.0, 1.0),
                sampling_noise_rms=SAMPLING_NOISE_RMS,
                comparator_noise_rms=COMPARATOR_NOISE_RMS,
                rng=np.random.default_rng(6000 + seed),
            )
            val_bits = sar_convert(
                sine_input(val_bin),
                actual,
                quant_range=(0.0, 1.0),
                sampling_noise_rms=SAMPLING_NOISE_RMS,
                comparator_noise_rms=COMPARATOR_NOISE_RMS,
                rng=np.random.default_rng(7000 + seed),
            )

            for harmonic_order in harmonic_orders:
                metrics = calibrate_and_evaluate(
                    train_bits,
                    val_bits,
                    actual,
                    train_bin,
                    harmonic_order,
                )
                rows.append(
                    {
                        "experiment": "external_h3",
                        "h3_dbc": "clean" if h3_level is None else h3_level,
                        "seed": seed,
                        "case": "calibrated",
                        "harmonic_order": harmonic_order,
                        **metrics,
                    }
                )
    return rows


def summarize(rows: list[dict]) -> dict:
    summary: dict[str, dict] = {}

    random_rows = [r for r in rows if r["experiment"] == "random_mismatch"]
    for sigma in sorted({r["sigma"] for r in random_rows}):
        sigma_rows = [r for r in random_rows if r["sigma"] == sigma and r["case"] == "calibrated"]
        summary[f"random_sigma_{sigma}"] = {}
        for harmonic_order in sorted({r["harmonic_order"] for r in sigma_rows}):
            h_rows = [r for r in sigma_rows if r["harmonic_order"] == harmonic_order]
            summary[f"random_sigma_{sigma}"][f"H{harmonic_order}"] = {
                "sfdr_dbc": quantiles([r["sfdr_dbc"] for r in h_rows]),
                "thd_dbc": quantiles([r["thd_dbc"] for r in h_rows]),
                "weight_shape_error": quantiles([r["weight_shape_error"] for r in h_rows]),
            }

    adversarial_rows = [r for r in rows if r["experiment"] == "adversarial_projection"]
    for label in sorted({r["harmonic_set"] for r in adversarial_rows}):
        label_rows = [r for r in adversarial_rows if r["harmonic_set"] == label]
        summary[f"adversarial_{label}"] = {
            "top_fixed_bit_projection": label_rows[0]["top_fixed_bit_projection"],
            "actual_projection": label_rows[0]["actual_projection"],
        }
        for harmonic_order in sorted({r["harmonic_order"] for r in label_rows if r["case"] == "calibrated"}):
            h_rows = [r for r in label_rows if r["harmonic_order"] == harmonic_order]
            summary[f"adversarial_{label}"][f"H{harmonic_order}"] = {
                "sfdr_dbc": h_rows[0]["sfdr_dbc"],
                "thd_dbc": h_rows[0]["thd_dbc"],
                "weight_shape_error": h_rows[0]["weight_shape_error"],
            }

    external_rows = [r for r in rows if r["experiment"] == "external_h3"]
    for h3_level in ["clean", -80, -70, -60, -50, -40]:
        level_rows = [r for r in external_rows if r["h3_dbc"] == h3_level]
        summary[f"external_h3_{h3_level}"] = {}
        for harmonic_order in sorted({r["harmonic_order"] for r in level_rows}):
            h_rows = [r for r in level_rows if r["harmonic_order"] == harmonic_order]
            summary[f"external_h3_{h3_level}"][f"H{harmonic_order}"] = {
                "sfdr_dbc": quantiles([r["sfdr_dbc"] for r in h_rows]),
                "thd_dbc": quantiles([r["thd_dbc"] for r in h_rows]),
                "weight_shape_error": quantiles([r["weight_shape_error"] for r in h_rows]),
            }

    return summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _, train_bin = find_coherent_frequency(FS, 6.1e6, N)
    _, val_bin = find_coherent_frequency(FS, 8.7e6, N)
    nominal_weights = sar_ideal_weights(ADC_BITS)

    rows = []
    rows.extend(experiment_random_mismatch(train_bin, val_bin, nominal_weights))
    rows.extend(experiment_adversarial_projection(train_bin, val_bin, nominal_weights))
    rows.extend(experiment_external_h3(train_bin, val_bin, nominal_weights))

    write_csv(OUTPUT_DIR / "results.csv", rows)
    summary = summarize(rows)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved: {OUTPUT_DIR / 'results.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'summary.json'}")


if __name__ == "__main__":
    main()
