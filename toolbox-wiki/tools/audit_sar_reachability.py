"""Audit simple SAR weight-list reachability margins.

This tool implements the interval check described in
``wiki/rigor/redundant_sar_reachability.md``. It is intentionally
dependency-free and operates on explicit positive SAR weights.

Examples:

    python tools/audit_sar_reachability.py
    python tools/audit_sar_reachability.py --weights 8,4,4,2,1
    python tools/audit_sar_reachability.py --weights 8,4,4,2,1 --error-budget 0.25
"""

from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditResult:
    name: str
    weights: tuple[float, ...]
    margins: tuple[float, ...]
    min_margin: float
    max_gap: float
    min_step: float
    max_step: float
    duplicate_codes: int


def parse_weights(text: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in text.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("weights must not be empty")
    if any((not math.isfinite(value)) or value <= 0 for value in values):
        raise argparse.ArgumentTypeError("weights must be positive finite numbers")
    return values


def normalize(weights: tuple[float, ...]) -> tuple[float, ...]:
    denom = sum(weights) + weights[-1]
    return tuple(value / denom for value in weights)


def branch_margins(weights: tuple[float, ...]) -> tuple[float, ...]:
    margins: list[float] = []
    for index, weight in enumerate(weights):
        future = sum(weights[index + 1 :])
        margins.append(future - weight)
    return tuple(margins)


def code_steps(weights: tuple[float, ...]) -> tuple[float, float, float, int]:
    if len(weights) > 24:
        raise ValueError("static code-step enumeration is limited to 24 weights")

    codes = sorted(
        sum(bit * weight for bit, weight in zip(bits, weights))
        for bits in itertools.product((0, 1), repeat=len(weights))
    )
    steps = [b - a for a, b in zip(codes, codes[1:])]
    positive_steps = [step for step in steps if step > 1e-15]
    duplicate_codes = len(steps) - len(positive_steps)
    if not positive_steps:
        return 0.0, 0.0, 0.0, duplicate_codes
    return max(positive_steps), min(positive_steps), max(positive_steps), duplicate_codes


def audit(name: str, raw_weights: tuple[float, ...]) -> AuditResult:
    weights = normalize(raw_weights)
    margins = branch_margins(weights)
    max_gap, min_step, max_step, duplicate_codes = code_steps(weights)
    return AuditResult(
        name=name,
        weights=weights,
        margins=margins,
        min_margin=min(margins),
        max_gap=max_gap,
        min_step=min_step,
        max_step=max_step,
        duplicate_codes=duplicate_codes,
    )


def format_weights(weights: tuple[float, ...]) -> str:
    return "[" + ", ".join(f"{value:.6g}" for value in weights) + "]"


def print_result(result: AuditResult, error_budget: float | None) -> None:
    print(f"\n[{result.name}]")
    print(f"normalized_weights = {format_weights(result.weights)}")
    print(f"branch_margins     = {format_weights(result.margins)}")
    print(f"min_margin         = {result.min_margin:.6g}")
    print(f"code_step_min/max  = {result.min_step:.6g} / {result.max_step:.6g}")
    print(f"duplicate_codes    = {result.duplicate_codes}")

    risky = [index for index, margin in enumerate(result.margins) if margin < 0]
    if risky:
        print(f"negative_margin_at = {risky}")
    else:
        print("negative_margin_at = []")

    if error_budget is not None:
        failed = [index for index, margin in enumerate(result.margins) if margin < error_budget]
        print(f"error_budget       = {error_budget:.6g}")
        print(f"budget_fail_bits   = {failed}")


def default_cases() -> list[tuple[str, tuple[float, ...]]]:
    return [
        ("binary_12b_with_half_lsb_style", tuple(float(2**i) for i in range(11, -1, -1))),
        ("duplicate_msb2_12b", (2048, 1024, 1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1)),
        (
            "radix18_integer_16b",
            (
                29127,
                16182,
                8990,
                4995,
                2775,
                1542,
                856,
                476,
                264,
                147,
                82,
                45,
                25,
                14,
                8,
                4,
                2,
                1,
            ),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--weights",
        type=parse_weights,
        help="comma-separated positive raw weights, e.g. 8,4,4,2,1",
    )
    parser.add_argument(
        "--name",
        default="custom",
        help="name used when --weights is supplied",
    )
    parser.add_argument(
        "--error-budget",
        type=float,
        help="optional normalized per-decision error budget to compare with margins",
    )
    args = parser.parse_args()

    if args.error_budget is not None and (
        not math.isfinite(args.error_budget) or args.error_budget < 0
    ):
        parser.error("--error-budget must be a finite non-negative number")

    cases = [(args.name, args.weights)] if args.weights else default_cases()
    for name, weights in cases:
        print_result(audit(name, weights), args.error_budget)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
