from app.backend.vision import LIMITATION_WARNING, image_quality, sample_image


def test_limitations_are_available():
    assert "Estimated visible skin appearance" in LIMITATION_WARNING


def test_quality_contract():
    report = image_quality(sample_image(128))
    assert "quality_score" in report
    assert "capture_quality_score" in report
