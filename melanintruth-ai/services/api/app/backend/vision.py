from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev

Pixel = tuple[int, int, int]
Image = list[list[Pixel]]
LIMITATION_WARNING = "Estimated visible skin appearance under standardised lighting assumptions; affected by lighting, exposure, camera sensor, white balance, HDR, compression, shadows, reflections, makeup, oil or sweat, lens quality, and device colour pipeline."
MIN_TEXTURE_ENERGY = 0.004


def flatten(image: Image) -> list[Pixel]:
    return [pixel for row in image for pixel in row]


def luminance(pixel: Pixel) -> float:
    return (0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]) / 255.0


def mean_rgb(image: Image) -> tuple[float, float, float]:
    pixels = flatten(image)
    return tuple(mean(p[i] for p in pixels) for i in range(3))  # type: ignore[return-value]


def brightness(image: Image) -> float:
    return mean(luminance(pixel) for pixel in flatten(image))


def contrast(image: Image) -> float:
    vals = [luminance(pixel) for pixel in flatten(image)]
    return pstdev(vals) if len(vals) > 1 else 0.0


def texture_energy(image: Image) -> float:
    total = 0.0
    count = 0
    for y, row in enumerate(image):
        for x, pixel in enumerate(row):
            if x + 1 < len(row):
                total += abs(luminance(pixel) - luminance(row[x + 1]))
                count += 1
            if y + 1 < len(image):
                total += abs(luminance(pixel) - luminance(image[y + 1][x]))
                count += 1
    return total / max(count, 1)


def histogram(image: Image, bins: int = 8) -> list[float]:
    counts = [0] * bins
    pixels = flatten(image)
    for pixel in pixels:
        idx = min(bins - 1, int(luminance(pixel) * bins))
        counts[idx] += 1
    return [count / len(pixels) for count in counts]


def image_quality(image: Image) -> dict[str, object]:
    b = brightness(image)
    c = contrast(image)
    t = texture_energy(image)
    reasons: list[str] = []
    advice: list[str] = []
    if b < 0.18:
        reasons.append("underexposure")
        advice.append("Retake with brighter indirect lighting.")
    if b > 0.86:
        reasons.append("overexposure")
        advice.append("Avoid harsh flash or glare.")
    if t < MIN_TEXTURE_ENERGY:
        reasons.append("blur_or_flat_detail_risk")
        advice.append("Hold the camera steady and keep natural texture visible.")
    if c > 0.35:
        reasons.append("shadow_or_highlight_risk")
        advice.append("Use more even lighting.")
    score = max(
        0.0,
        min(
            1.0,
            0.45
            + (0.25 - abs(b - 0.55))
            + min(t * 8, 0.2)
            - max(c - 0.25, 0),
        ),
    )
    return {
        "quality_score": score,
        "failure_reasons": reasons,
        "retake_advice": advice,
        "suitable_for_analysis": score >= 0.45 and not reasons,
        "capture_quality_score": score,
        "confidence_score": score,
    }


@dataclass(frozen=True)
class SafetyCheck:
    name: str
    passed: bool
    value: float
    threshold: float
    explanation: str


class SafetyGate:
    def evaluate(self, original: Image, rendered: Image, confidence: float) -> dict[str, object]:
        o_rgb = mean_rgb(original)
        r_rgb = mean_rgb(rendered)
        tone_delta = sum(abs(o_rgb[i] - r_rgb[i]) for i in range(3)) / 3 / 255
        original_texture = texture_energy(original)
        rendered_texture = texture_energy(rendered)
        texture_similarity = (
            1.0
            if original_texture == 0
            else min(rendered_texture, original_texture)
            / max(rendered_texture, original_texture)
        )
        original_contrast = contrast(original)
        rendered_contrast = contrast(rendered)
        local_contrast = (
            1.0
            if original_contrast == 0
            else min(original_contrast, rendered_contrast)
            / max(original_contrast, rendered_contrast)
        )
        hist_shift = sum(
            abs(a - b) for a, b in zip(histogram(original), histogram(rendered))
        ) / 2
        brightness_shift = abs(brightness(original) - brightness(rendered))
        checks = [
            SafetyCheck(
                "skin_tone_delta",
                tone_delta <= 0.08,
                tone_delta,
                0.08,
                "Skin tone shift must stay within standardised-lighting bounds.",
            ),
            SafetyCheck(
                "texture_similarity",
                texture_similarity >= 0.92,
                texture_similarity,
                0.92,
                "Natural pores, marks, scars, and pigmentation texture must be preserved.",
            ),
            SafetyCheck(
                "edge_preservation",
                texture_similarity >= 0.90,
                texture_similarity,
                0.90,
                "Edges and identity-bearing details must remain intact.",
            ),
            SafetyCheck(
                "local_contrast_preservation",
                local_contrast >= 0.85,
                local_contrast,
                0.85,
                "Local contrast cannot be flattened like a smoothing filter.",
            ),
            SafetyCheck(
                "histogram_shift",
                hist_shift <= 0.20,
                hist_shift,
                0.20,
                "Skin histogram cannot shift excessively.",
            ),
            SafetyCheck(
                "confidence_threshold",
                confidence >= 0.55,
                confidence,
                0.55,
                "Low confidence renders must be blocked.",
            ),
            SafetyCheck(
                "brightness_shift",
                brightness_shift <= 0.12,
                brightness_shift,
                0.12,
                "Brightness correction cannot lighten or darken excessively.",
            ),
            SafetyCheck(
                "excessive_smoothing",
                rendered_texture >= original_texture * 0.75,
                rendered_texture,
                original_texture * 0.75,
                "Rendering cannot smooth visible skin texture.",
            ),
        ]
        failed = [check for check in checks if not check.passed]
        risk = (
            "low"
            if not failed
            else (
                "blocked"
                if len(failed) >= 2
                or any(
                    c.name
                    in {
                        "skin_tone_delta",
                        "excessive_smoothing",
                        "confidence_threshold",
                    }
                    for c in failed
                )
                else "high"
            )
        )
        return {
            "passed": not failed,
            "checks": [c.__dict__ for c in checks],
            "failed_checks": [c.name for c in failed],
            "risk_level": risk,
            "explanation": "No-beautification safety gate blocks whitening, smoothing, excessive lighting correction, identity alteration, and unsafe confidence.",
            "recommendation": (
                "Return original or request retake; do not present blocked render as valid output."
                if failed
                else "Render may be presented with limitations."
            ),
        }


def sample_image(value: int = 128, size: int = 16) -> Image:
    """Create a deterministic, textured baseline image for quality-gate tests.

    The checkerboard variation preserves visible local detail without altering the
    requested mean tone, while extreme values still correctly trigger exposure
    rejection.
    """
    delta = 8 if 8 <= value <= 247 else 0
    return [
        [
            (
                max(0, min(255, value + (delta if (x + y) % 2 == 0 else -delta))),
                max(0, min(255, value + (delta if (x + y) % 2 == 0 else -delta))),
                max(0, min(255, value + (delta if (x + y) % 2 == 0 else -delta))),
            )
            for x in range(size)
        ]
        for y in range(size)
    ]
