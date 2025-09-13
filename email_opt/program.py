import dspy
from .signatures import DraftEmail, CritiqueEmail, RewriteEmail

class EmailProgram(dspy.Module):
    def __init__(self):
        super().__init__()
        self.writer = dspy.Predict(DraftEmail)
        self.critic = dspy.Predict(CritiqueEmail)
        self.rewriter = dspy.Predict(RewriteEmail)

    def forward(self, **slots):
        draft = self.writer(**slots)
        crit = self.critic(subject=draft.subject, body=draft.body)
        final = self.rewriter(subject=draft.subject, body=draft.body, feedback=crit.feedback)
        return dspy.Prediction(
            subject=final.subject_new,
            body=final.body_new,
            feedback=crit.feedback
        )
