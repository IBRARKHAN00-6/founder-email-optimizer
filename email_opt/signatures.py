from typing import Optional
import dspy

# Writer: produces subject + body using structured slots + template
class DraftEmail(dspy.Signature):
    """Write a YC-founder-friendly cold email: ≤120 words, 1 metric of proof, 1 clear CTA.
    No fluff. Be specific and polite. Keep subject ≤6 words, no clickbait."""
    first_name: str = dspy.InputField()
    company: str = dspy.InputField()
    persona: Optional[str] = dspy.InputField()
    pain: Optional[str] = dspy.InputField()
    product: Optional[str] = dspy.InputField()
    product_value: Optional[str] = dspy.InputField()
    customer_example: Optional[str] = dspy.InputField()
    impact_metric: Optional[str] = dspy.InputField()
    template: str = dspy.InputField()
    subject: str = dspy.OutputField(desc="Catchy, specific, ≤6 words")
    body: str = dspy.OutputField(desc="Email body plain text")

# Critic: suggests concrete adjustments
class CritiqueEmail(dspy.Signature):
    """Critique for tone, specificity, proof, CTA, and length."""
    subject: str = dspy.InputField()
    body: str = dspy.InputField()
    feedback: str = dspy.OutputField(desc="JSON: {tone, specificity, proof, CTA, length}")

# Rewriter: applies the critique
class RewriteEmail(dspy.Signature):
    """Rewrite using feedback; preserve facts and constraints."""
    subject: str = dspy.InputField()
    body: str = dspy.InputField()
    feedback: str = dspy.InputField()
    subject_new: str = dspy.OutputField()
    body_new: str = dspy.OutputField()

# Slot extractor: turns 'winner' emails into structured slots for training
class ExtractSlots(dspy.Signature):
    """Extract slots from a winning sales email. Return JSON keys:
    {persona, pain, product, product_value, customer_example, impact_metric}"""
    subject: str = dspy.InputField()
    body: str = dspy.InputField()
    slots_json: str = dspy.OutputField()

# Judge: returns JSON {score: int(0-10), reason: str}
class JudgeEmail(dspy.Signature):
    """Score for YC founders: brevity, specificity, proof (numbers), peer signal, clear CTA."""
    subject: str = dspy.InputField()
    body: str = dspy.InputField()
    json: str = dspy.OutputField()
