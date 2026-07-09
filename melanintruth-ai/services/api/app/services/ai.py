from dataclasses import dataclass
import numpy as np
from skimage import color, filters, feature, metrics

LIMITATION = "Estimated visible skin appearance under standardised lighting assumptions; affected by lighting, exposure, sensor, white balance, HDR, compression, shadows, reflections, makeup, oil or sweat, lens quality, and device colour pipeline."

@dataclass(frozen=True)
class QualityReport:
    quality_score: float; failure_reasons: list[str]; retake_advice: list[str]; suitable_for_analysis: bool; suitable_for_progress_tracking: bool; suitable_for_makeup_matching: bool; confidence_score: float

def image_quality(image: np.ndarray) -> QualityReport:
    gray = color.rgb2gray(image[..., :3]) if image.ndim == 3 else image
    blur = float(filters.laplace(gray).var())
    mean = float(gray.mean()); std = float(gray.std())
    reasons=[]; advice=[]
    if blur < 0.0005: reasons.append("blur_risk"); advice.append("Retake with a steady camera and clean lens.")
    if mean < 0.18: reasons.append("underexposure"); advice.append("Use brighter indirect lighting.")
    if mean > 0.86: reasons.append("overexposure"); advice.append("Avoid harsh flash or direct glare.")
    if std > 0.33: reasons.append("shadow_or_highlight_risk"); advice.append("Use even lighting without strong shadows.")
    score=max(0.0,min(1.0,0.25+mean*(1-abs(std-0.18))+min(blur*250,0.35)))
    return QualityReport(score,reasons,advice,score>=0.45,score>=0.60,score>=0.65,score)

def lighting_estimate(image: np.ndarray) -> dict[str, float | str]:
    rgb=image[..., :3].astype(float)/255 if image.max()>1 else image[..., :3].astype(float)
    means=rgb.reshape(-1,3).mean(axis=0); brightness=float(means.mean()); contrast=float(rgb.std())
    cast_idx=int(np.argmax(np.abs(means-means.mean()))); cast=["red","green","blue"][cast_idx]
    return {"brightness":brightness,"contrast":contrast,"likely_colour_cast":cast,"shadow_risk":min(1.0,contrast*2),"highlight_risk":float((rgb>0.93).mean()),"white_balance_confidence":1-float(np.std(means)),"standardisation_suitability":max(0.0,1-abs(brightness-0.55)-contrast/2)}

def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    arr=np.asarray(rgb, dtype=float); arr = arr/255 if arr.max()>1 else arr
    return color.rgb2lab(arr.reshape(1,1,3)).reshape(3)

def delta_e(rgb_a: np.ndarray, rgb_b: np.ndarray) -> float: return float(color.deltaE_ciede2000(srgb_to_lab(rgb_a), srgb_to_lab(rgb_b)))
def ita(rgb: np.ndarray) -> dict[str, float | str]:
    lab=srgb_to_lab(rgb); val=float(np.degrees(np.arctan2(lab[0]-50, lab[2] if lab[2] != 0 else 1e-6)))
    return {"ita":val,"limitation":LIMITATION}
def undertone(rgb: np.ndarray) -> dict[str, float | str]:
    lab=srgb_to_lab(rgb); tone="neutral" if abs(lab[2])<5 else ("golden" if lab[2]>0 else "cool/red")
    return {"estimate": tone, "confidence": max(0.2, min(0.8, abs(float(lab[2]))/30))}
def segment_skin_baseline(image: np.ndarray) -> dict[str, object]:
    rgb=image[..., :3].astype(float)/255 if image.max()>1 else image[..., :3].astype(float)
    mask=np.ones(rgb.shape[:2], dtype=bool)  # inclusive baseline: do not exclude dark, vitiligo, pigmentation regions.
    return {"skin_mask":mask,"confidence_mask":np.full(mask.shape,0.55),"excluded_regions":[],"region_statistics":{"coverage":float(mask.mean())},"failure_reasons":[]}
def safety_gate(original: np.ndarray, rendered: np.ndarray, confidence: float, tone_threshold: float=8.0) -> dict[str, object]:
    o=original[..., :3].astype(float)/255 if original.max()>1 else original[..., :3].astype(float)
    r=rendered[..., :3].astype(float)/255 if rendered.max()>1 else rendered[..., :3].astype(float)
    tone=delta_e(o.reshape(-1,3).mean(axis=0), r.reshape(-1,3).mean(axis=0))
    texture=metrics.structural_similarity(color.rgb2gray(o), color.rgb2gray(r), data_range=1.0)
    edges=metrics.structural_similarity(feature.canny(color.rgb2gray(o)).astype(float), feature.canny(color.rgb2gray(r)).astype(float), data_range=1.0)
    rejected = tone>tone_threshold or texture<0.94 or edges<0.90 or confidence<0.55
    reasons=[]
    if tone>tone_threshold: reasons.append("skin_tone_delta_exceeds_threshold")
    if texture<0.94: reasons.append("texture_similarity_below_threshold")
    if edges<0.90: reasons.append("edge_preservation_below_threshold")
    if confidence<0.55: reasons.append("confidence_too_low")
    return {"accepted":not rejected,"reasons":reasons,"skin_tone_delta":tone,"texture_similarity":float(texture),"edge_preservation":float(edges)}
def authentic_render(image: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    estimate=lighting_estimate(image); confidence=float(estimate["standardisation_suitability"])
    rendered=image.copy()  # baseline preserves pixels; trained D65 adapter plugs in here.
    return rendered,{"confidence_score":confidence,"uncertainty_score":1-confidence,"explanation":LIMITATION,"transformation":"identity_preserving_baseline"}
