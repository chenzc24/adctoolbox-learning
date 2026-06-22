"""Dynamic range sweep extended into the clipping region.

Extends exp_s04_sweep_dynamic_range.py past 0 dBFS to reveal how clipping
degrades THD / SFDR / SNDR while SNR keeps rising.

Run from the Python package directory:

    cd E:/ADCToolbox/python
    uv run python ../learning/adctoolbox-learning/demos/exp_s04_dynamic_range_with_clipping.py

Output is saved under learning/adctoolbox-learning/outputs/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from adctoolbox import amplitudes_to_snr, analyze_spectrum, find_coherent_frequency

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "dynamic_range_clipping"

N_fft = 2 ** 13
Fs = 100e6
Fin_target = 12e6
Fin, Fin_bin = find_coherent_frequency(fs=Fs, fin_target=Fin_target, n_fft=N_fft)

# Fixed noise floor (same as the original exp_s04)
noise_rms = 100e-6  # 100 uVrms

# Full-scale is [-0.5, +0.5], so 0 dBFS = A=0.5.
# Sweep from -60 dBFS up to +12 dBFS so we cross the clipping threshold.
amplitudes_dbfs = np.linspace(-60, 12, 73)
amplitudes = 0.5 * 10 ** (amplitudes_dbfs / 20)

print(f"[Setup] Fs={Fs/1e6:.0f} MHz, N={N_fft}, Fin={Fin/1e6:.6f} MHz (bin {Fin_bin})")
print(f"[Setup] full-scale range = [-0.5, +0.5] V, 0 dBFS = A=0.5 Vpeak")
print(f"[Setup] fixed noise_rms = {noise_rms*1e6:.0f} uVrms")
print(f"[Setup] sweeping {len(amplitudes_dbfs)} amplitudes from "
      f"{amplitudes_dbfs[0]:.1f} to {amplitudes_dbfs[-1]:.1f} dBFS\n")

t = np.arange(N_fft) / Fs
rng = np.random.default_rng(20260622)

# Containers
snr, sndr, thd, sfdr, enob = [], [], [], [], []
snr_theory = []

# Track whether each point actually clipped
clip_flags = []

for A, A_dbfs in zip(amplitudes, amplitudes_dbfs):
    # Ideal sine (peak A), then add the same fixed noise
    raw = A * np.sin(2 * np.pi * Fin * t)
    sig = raw + rng.standard_normal(N_fft) * noise_rms

    # Emulate ADC clipping at the full-scale edges [-0.5, +0.5]
    clipped = np.clip(sig, -0.5, 0.5)
    n_clipped = int(np.sum(np.abs(sig) > 0.5))
    clip_flags.append(n_clipped)

    # analyze_spectrum uses max_scale_range to set the dBFS reference
    result = analyze_spectrum(
        clipped,
        fs=Fs,
        max_scale_range=[-0.5, 0.5],
        create_plot=False,
    )

    snr.append(result["snr_dbc"])
    sndr.append(result["sndr_dbc"])
    thd.append(result["thd_dbc"])
    sfdr.append(result["sfdr_dbc"])
    enob.append(result["enob"])
    snr_theory.append(amplitudes_to_snr(sig_amplitude=A, noise_amplitude=noise_rms))

snr = np.array(snr)
sndr = np.array(sndr)
thd = np.array(thd)
sfdr = np.array(sfdr)
enob = np.array(enob)
snr_theory = np.array(snr_theory)
clip_flags = np.array(clip_flags)

# Find the "sweet spot": the amplitude where SNDR peaks
idx_best = int(np.argmax(sndr))
print(
    f"[Sweet spot] SNDR peaks at {amplitudes_dbfs[idx_best]:+.1f} dBFS: "
    f"SNDR={sndr[idx_best]:.2f} dB, ENOB={enob[idx_best]:.2f} b, "
    f"SNR={snr[idx_best]:.2f} dB, THD={thd[idx_best]:.2f} dB, SFDR={sfdr[idx_best]:.2f} dB"
)

# Clip-rate at the sweet spot and a few points past it
print("\n[Clipping samples per record]")
for i in [idx_best - 4, idx_best, idx_best + 4, idx_best + 8, -1]:
    if 0 <= i < len(amplitudes_dbfs):
        pct = 100 * clip_flags[i] / N_fft
        print(f"  A={amplitudes_dbfs[i]:+6.1f} dBFS -> {clip_flags[i]:5d} samples clipped ({pct:5.2f}%)")

# ---- Plot: 2 panels ----
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9), sharex=True)

# Top panel: SNR, SNDR, ENOB (twin)
color_snr = "tab:blue"
color_sndr = "tab:red"
ax1.set_xlabel("Amplitude (dBFS)")
ax1.set_ylabel("SNR / SNDR (dB)", color=color_snr)
ax1.plot(amplitudes_dbfs, snr_theory, "--", color="black", alpha=0.5, label="Theory SNR (no clip)")
ax1.plot(amplitudes_dbfs, snr, "o-", color=color_snr, markersize=3, label="Measured SNR")
ax1.plot(amplitudes_dbfs, sndr, "s-", color=color_sndr, markersize=3, label="Measured SNDR")
ax1.tick_params(axis="y", labelcolor=color_snr)
ax1.grid(True, alpha=0.3)
ax1.axvline(x=0, color="gray", linestyle=":", alpha=0.6, label="0 dBFS (full-scale)")
ax1.axvline(x=amplitudes_dbfs[idx_best], color="green", linestyle=":", alpha=0.6,
            label=f"sweet spot ({amplitudes_dbfs[idx_best]:+.1f} dBFS)")
ax1.legend(loc="upper left", fontsize=9)
ax1.set_ylim(-10, 90)
ax1.set_title("SNR keeps rising, SNDR peaks then collapses past clipping", fontsize=11)

ax1b = ax1.twinx()
color_enob = "tab:purple"
ax1b.set_ylabel("ENOB (bits)", color=color_enob)
ax1b.plot(amplitudes_dbfs, enob, "^-", color=color_enob, markersize=3, label="ENOB (from SNDR)")
ax1b.tick_params(axis="y", labelcolor=color_enob)
ax1b.legend(loc="lower right", fontsize=9)

# Bottom panel: THD, SFDR
ax2.set_xlabel("Amplitude (dBFS)")
ax2.set_ylabel("THD / SFDR (dBc)")
ax2.plot(amplitudes_dbfs, thd, "v-", color="tab:orange", markersize=3, label="THD (lower is worse)")
ax2.plot(amplitudes_dbfs, sfdr, "d-", color="tab:green", markersize=3, label="SFDR (lower is worse)")
ax2.axvline(x=0, color="gray", linestyle=":", alpha=0.6)
ax2.axvline(x=amplitudes_dbfs[idx_best], color="green", linestyle=":", alpha=0.6)
ax2.axhline(y=0, color="k", linewidth=0.5)
ax2.grid(True, alpha=0.3)
ax2.legend(loc="lower left", fontsize=9)
ax2.set_ylim(-60, 120)
ax2.set_title("Clipping pushes THD/SFDR through the floor", fontsize=11)

plt.tight_layout()
out = OUTPUT_DIR / "dynamic_range_with_clipping.png"
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=150)
plt.close(fig)
print(f"\n[Save fig] -> {out}")
