import json, re
import dspy
from .signatures import JudgeEmail

SPAMMY = {"free","guarantee","winner","act now","limited time","cheap","exclusive"}
FLUFFY = {"innovative","cutting-edge","disruptive","revolutionary","groundbreaking"}

def hard_checks(subject: str, body: str) -> int:
    score = 10
    words = len(body.split())
    if words > 120: score -= 3
    if len(subject.split()) > 6: score -= 1
    if any(w in body.lower() for w in SPAMMY): score -= 2
    if any(w in body.lower() for w in FLUFFY): score -= 1
    if not re.search(r"\d{1,3}%|\d+(\.\d+)?\s*(x|hrs?|days?)", body.lower()):  # no numbers/metrics
        score -= 2
    if "?" not in body: score -= 1  # weak CTA proxy
    return max(0, min(10, score))

_llm_judge = dspy.Predict(JudgeEmail)

def llm_judge(subject: str, body: str):
    j = _llm_judge(subject=subject, body=body).json.strip()
    try:
        data = json.loads(j)
        return int(data.get("score", 6)), data.get("reason", "ok")
    except Exception:
        return 6, "fallback"

def scoring_metric(example, pred, trace=None) -> float:
    s_llm, _ = llm_judge(pred.subject, pred.body)
    s_hard = hard_checks(pred.subject, pred.body)
    return round(0.7 * s_llm + 0.3 * s_hard, 2)
