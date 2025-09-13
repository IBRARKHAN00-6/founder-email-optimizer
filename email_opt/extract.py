import json
import dspy
from .signatures import ExtractSlots

_extractor = dspy.ChainOfThought(ExtractSlots)

def extract_slots_from_winner(subject: str, body: str) -> dict:
    out = _extractor(subject=subject, body=body).slots_json.strip()
    try:
        slots = json.loads(out)
    except Exception:
        slots = {}
    # Coerce to known keys
    keys = ["persona","pain","product","product_value","customer_example","impact_metric"]
    return {k: (slots.get(k) or "") for k in keys}
