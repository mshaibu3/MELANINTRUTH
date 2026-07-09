from app.backend.vision import SafetyGate, sample_image


def test_render_rejects_skin_tone_shift():
    report = SafetyGate().evaluate(sample_image(80), sample_image(180), 0.9)
    assert "skin_tone_delta" in report["failed_checks"]


def test_render_rejects_low_confidence():
    report = SafetyGate().evaluate(sample_image(128), sample_image(128), 0.1)
    assert "confidence_threshold" in report["failed_checks"]
