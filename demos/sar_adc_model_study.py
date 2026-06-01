"""Learn a SAR ADC model with ADCToolbox.

Run from the Python package directory:

    cd E:/ADCToolbox/python
    uv run python ../agent_playground/adctoolbox_learning/demos/sar_adc_model_study.py

This playground is intentionally outside tracked source. It demonstrates the
main pieces of an ADC behavioral model:

1. Generate a coherent input sine.
2. Build ideal SAR CDAC weights.
3. Add capacitor mismatch and input/comparator noise.
4. Convert analog samples to bit decisions.
5. Reconstruct digital output from the bits.
6. Measure SNDR/SNR/SFDR/ENOB with ADCToolbox.
7. Print the SAR bit-trial sequence for one selected sample.
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from adctoolbox import analyze_spectrum, calibrate_weight_sine
from adctoolbox.models import (
    sar_apply_cap_mismatch,
    sar_convert,
    sar_ideal_weights,
    sar_reconstruct,
)


@dataclass(frozen=True)
class ADCConfig:
    """Knobs to edit first while learning."""

    num_bits: int = 12
    fs: float = 100e6
    n_samples: int = 2**14
    fin_bin: int = 997
    input_dc: float = 0.5
    input_amplitude: float = 0.49
    cap_mismatch_sigma: float = 0.002
    sampling_noise_rms: float = 30e-6
    comparator_noise_rms: float = 30e-6
    rng_seed: int = 20260530


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "sar_adc_model"
CFG = ADCConfig()


def make_coherent_input(cfg: ADCConfig) -> tuple[np.ndarray, float]:
    """A coherent sine lands exactly on one FFT bin."""
    n = np.arange(cfg.n_samples)
    fin = cfg.fin_bin * cfg.fs / cfg.n_samples
    vin = cfg.input_dc + cfg.input_amplitude * np.sin(
        2.0 * np.pi * cfg.fin_bin * n / cfg.n_samples
    )
    return vin, fin


def sar_trial_trace(vin_sample: float, weights: np.ndarray) -> list[dict]:
    """Show every SAR decision for one sample.

    This mirrors the model in adctoolbox.models.sar_convert, without random
    noise. It is useful for learning what the bit decisions mean.
    """
    v_dac = 0.0
    rows = []
    for bit_index, weight in enumerate(weights):
        v_test = v_dac + weight
        bit = int(vin_sample >= v_test)
        if bit:
            v_dac = v_test
        rows.append(
            {
                "bit_index": bit_index,
                "weight": weight,
                "v_test": v_test,
                "bit": bit,
                "v_dac_after": v_dac,
                "residue": vin_sample - v_dac,
            }
        )
    return rows


def reconstruct_centered(bits: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Convert bits back to an analog estimate and remove DC."""
    aout = sar_reconstruct(bits, weights, quant_range=(0.0, 1.0))
    return aout - np.mean(aout)


def run_spectrum(signal: np.ndarray, cfg: ADCConfig, ax, title: str) -> dict:
    """Measure ADC dynamic metrics."""
    metrics = analyze_spectrum(
        signal,
        fs=cfg.fs,
        max_scale_range=(-0.5, 0.5),
        win_type="rectangular",
        side_bin=0,
        max_harmonic=5,
        nf_method=3,
        create_plot=True,
        show_label=True,
        ax=ax,
    )
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_ylim(-155, 5)
    return metrics


def print_metrics(name: str, metrics: dict) -> None:
    print(
        f"{name:<36} "
        f"SNDR={metrics['sndr_dbc']:7.2f} dB  "
        f"SNR={metrics['snr_dbc']:7.2f} dB  "
        f"SFDR={metrics['sfdr_dbc']:7.2f} dB  "
        f"ENOB={metrics['enob']:6.2f} bits"
    )


def print_trial_trace(vin_sample: float, rows: list[dict]) -> None:
    print()
    print(f"SAR bit-trial trace for one sample, vin={vin_sample:.6f}")
    print("bit  weight      v_test      decision  v_dac_after  residue")
    print("---  ----------  ----------  --------  -----------  ----------")
    for row in rows:
        print(
            f"{row['bit_index']:>3d}  "
            f"{row['weight']:>10.7f}  "
            f"{row['v_test']:>10.7f}  "
            f"{row['bit']:>8d}  "
            f"{row['v_dac_after']:>11.7f}  "
            f"{row['residue']:>10.7f}"
        )


def save_learning_plots(
    cfg: ADCConfig,
    vin: np.ndarray,
    ideal_aout: np.ndarray,
    nonideal_aout: np.ndarray,
    calibrated_aout: np.ndarray,
    metrics_by_name: dict[str, dict],
) -> None:
    """Save a time-domain comparison and a spectrum comparison."""
    n_plot = 220
    t_ns = np.arange(n_plot) / cfg.fs * 1e9

    fig, ax = plt.subplots(figsize=(11, 4.2), constrained_layout=True)
    ax.plot(t_ns, vin[:n_plot] - np.mean(vin), label="input, centered", linewidth=1.7)
    ax.step(t_ns, ideal_aout[:n_plot], where="mid", label="ideal SAR output", linewidth=1.2)
    ax.step(
        t_ns,
        nonideal_aout[:n_plot],
        where="mid",
        label="nonideal, nominal weights",
        linewidth=1.2,
    )
    ax.set_title("Time-domain ADC input/output comparison", fontweight="bold")
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Centered voltage")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.savefig(OUTPUT_DIR / "01_time_domain.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8), constrained_layout=True)
    run_spectrum(ideal_aout, cfg, axes[0], "Ideal SAR")
    run_spectrum(nonideal_aout, cfg, axes[1], "Mismatch + Noise")
    run_spectrum(calibrated_aout, cfg, axes[2], "Sine-Calibrated Bits")
    fig.suptitle(
        f"{cfg.num_bits}-bit SAR ADC spectra, Fin/Fs={cfg.fin_bin}/{cfg.n_samples}",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(OUTPUT_DIR / "02_spectrum_comparison.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    with open(OUTPUT_DIR / "metrics_summary.csv", "w", encoding="ascii") as f:
        f.write("case,sndr_dbc,snr_dbc,sfdr_dbc,enob\n")
        for name, metrics in metrics_by_name.items():
            f.write(
                f"{name},{metrics['sndr_dbc']:.6f},{metrics['snr_dbc']:.6f},"
                f"{metrics['sfdr_dbc']:.6f},{metrics['enob']:.6f}\n"
            )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    cfg = CFG
    rng = np.random.default_rng(cfg.rng_seed)
    vin, fin = make_coherent_input(cfg)

    nominal_weights = sar_ideal_weights(cfg.num_bits)
    actual_weights = sar_apply_cap_mismatch(
        nominal_weights,
        sigma=cfg.cap_mismatch_sigma,
        rng=rng,
    )

    ideal_bits = sar_convert(vin, nominal_weights, quant_range=(0.0, 1.0))
    nonideal_bits = sar_convert(
        vin,
        actual_weights,
        quant_range=(0.0, 1.0),
        sampling_noise_rms=cfg.sampling_noise_rms,
        comparator_noise_rms=cfg.comparator_noise_rms,
        rng=rng,
    )

    ideal_aout = reconstruct_centered(ideal_bits, nominal_weights)
    nonideal_aout = reconstruct_centered(nonideal_bits, nominal_weights)

    # This estimates digital weights from the raw bit columns and a sine input.
    # It is useful for learning how foreground calibration improves a SAR model.
    cal = calibrate_weight_sine(
        nonideal_bits,
        freq=cfg.fin_bin / cfg.n_samples,
        harmonic_order=3,
        verbose=0,
    )
    calibrated_aout = np.asarray(cal["calibrated_signal"], dtype=float)
    calibrated_aout = calibrated_aout - np.mean(calibrated_aout)

    # Actual-weight reconstruction is an oracle reference. Real silicon would
    # not know these weights unless measured or calibrated.
    actual_weight_aout = reconstruct_centered(nonideal_bits, actual_weights)

    fig, axes = plt.subplots(1, 4, figsize=(21, 4.8), constrained_layout=True)
    metrics = {
        "ideal": run_spectrum(ideal_aout, cfg, axes[0], "Ideal SAR"),
        "nonideal_nominal": run_spectrum(nonideal_aout, cfg, axes[1], "Nonideal, Nominal Weights"),
        "sine_calibrated": run_spectrum(calibrated_aout, cfg, axes[2], "Sine-Calibrated Bits"),
        "actual_weight_oracle": run_spectrum(
            actual_weight_aout,
            cfg,
            axes[3],
            "Actual-Weight Oracle",
        ),
    }
    fig.suptitle(
        (
            f"{cfg.num_bits}-bit SAR model, Fin={fin / 1e6:.3f} MHz, "
            f"sigma_Cu={cfg.cap_mismatch_sigma * 100:.3f}%"
        ),
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(OUTPUT_DIR / "00_main_spectrum_summary.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    save_learning_plots(cfg, vin, ideal_aout, nonideal_aout, calibrated_aout, metrics)

    trace_index = cfg.n_samples // 7
    trace_rows = sar_trial_trace(float(vin[trace_index]), nominal_weights)
    print_trial_trace(float(vin[trace_index]), trace_rows)

    np.savez_compressed(
        OUTPUT_DIR / "sar_adc_learning_data.npz",
        vin=vin,
        ideal_bits=ideal_bits,
        nonideal_bits=nonideal_bits,
        ideal_aout=ideal_aout,
        nonideal_aout=nonideal_aout,
        calibrated_aout=calibrated_aout,
        actual_weight_aout=actual_weight_aout,
        nominal_weights=nominal_weights,
        actual_weights=actual_weights,
        calibrated_weights=cal["weight"],
        fs=cfg.fs,
        fin=fin,
    )

    print()
    print(f"ADC model: {cfg.num_bits} bits, Fs={cfg.fs / 1e6:.3f} MHz, Fin={fin / 1e6:.3f} MHz")
    print(
        "Non-idealities: "
        f"sigma_Cu={cfg.cap_mismatch_sigma * 100:.3f}%, "
        f"sampling_noise={cfg.sampling_noise_rms * 1e6:.1f} uVrms, "
        f"comparator_noise={cfg.comparator_noise_rms * 1e6:.1f} uVrms"
    )
    print()
    print_metrics("Ideal", metrics["ideal"])
    print_metrics("Nonideal, nominal weights", metrics["nonideal_nominal"])
    print_metrics("Sine-calibrated bits", metrics["sine_calibrated"])
    print_metrics("Actual-weight oracle", metrics["actual_weight_oracle"])
    print()
    print(f"Outputs saved under: {OUTPUT_DIR}")
    print("Edit ADCConfig near the top of this file to change the model.")


if __name__ == "__main__":
    main()
