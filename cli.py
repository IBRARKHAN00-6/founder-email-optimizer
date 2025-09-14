import os, argparse, json, pandas as pd
from dotenv import load_dotenv
import dspy

from email_opt.program import EmailProgram
from email_opt.extract import extract_slots_from_winner
from email_opt.judge import scoring_metric

def configure_lm():
    load_dotenv()
    model_id = os.getenv("MODEL_ID", "openai/gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY", os.getenv("API_KEY", ""))
    api_base = os.getenv("API_BASE", None)
    lm = dspy.LM(model_id, api_key=api_key, api_base=api_base, model_type="chat")
    dspy.configure(lm=lm)  # modern DSPy configure
    return lm

def row_to_example(slots: dict, template: str, subject: str, body: str):
    fields = ["first_name","company","persona","pain","product",
              "product_value","customer_example","impact_metric"]
    filled = {k: slots.get(k, "") for k in fields}
    filled["template"] = template
    ex = dspy.Example(**filled, subject=subject, body=body).with_inputs(*([*fields, "template"]))
    return ex

def build_trainset_from_wins(wins_df: pd.DataFrame, template: str):
    train = []
    for _, r in wins_df.iterrows():
        subj = str(r.get("subject", "")).strip()
        body = str(r.get("body", "")).strip()
        slots = extract_slots_from_winner(subj, body)
        # use neutral placeholders to avoid overfitting to names
        slots.setdefault("first_name", "Alex")
        slots.setdefault("company", "BatchmateX")
        train.append(row_to_example(slots, template, subj, body))
    return train

def gepa_metric_wrapper(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """Wrapper for GEPA which requires 5 parameters but sometimes only passes 2"""
    # Handle both calling conventions
    if trace is None:
        # Called with just (gold, pred) during evaluation
        return scoring_metric(gold, pred)
    else:
        # Called with all 5 parameters during optimization
        return scoring_metric(gold, pred, trace)

def compile_program(trainset, optimizer: str):
    prog = EmailProgram()
    if optimizer == "none" or len(trainset) == 0:
        return prog
    if optimizer == "bootstrap":
        tele = dspy.BootstrapFewShot(metric=scoring_metric, max_bootstrapped_demos=min(4, len(trainset)))
        return tele.compile(prog, trainset=trainset)
    if optimizer == "gepa":
        # GEPA requires a reflection LM - use the same model with higher temperature
        reflection_lm = dspy.LM(
            model=os.getenv("MODEL_ID", "openai/gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY", os.getenv("API_KEY", "")),
            api_base=os.getenv("API_BASE", None),
            temperature=1.0,
            max_tokens=2000
        )
        tele = dspy.GEPA(
            metric=gepa_metric_wrapper,
            reflection_lm=reflection_lm,
            track_stats=True,
            auto="light"
        )
        # use same tiny set for val to keep v0 simple
        return tele.compile(prog, trainset=trainset, valset=trainset)
    # mipro
    tele = dspy.MIPROv2(metric=scoring_metric, auto="light", num_candidates=4, init_temperature=1.0)
    # use same tiny set for val to keep v0 simple
    return tele.compile(prog, trainset=trainset, valset=trainset, num_trials=6)

def generate_for_leads(prog, leads_df: pd.DataFrame, template: str):
    outs = []
    for _, r in leads_df.iterrows():
        slots = {k: str(r.get(k, "") or "") for k in [
            "first_name","company","persona","pain","product","product_value","customer_example","impact_metric"
        ]}
        slots["template"] = template
        pred = prog(**slots)
        score = scoring_metric(None, pred)
        outs.append({
            **r.to_dict(),
            "optimized_subject": pred.subject,
            "optimized_body": pred.body,
            "score_0_10": score,
            "feedback": pred.feedback
        })
    return pd.DataFrame(outs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wins", default="wins.csv", help="CSV with columns: subject, body")
    ap.add_argument("--leads", default="leads.csv", help="CSV of leads")
    ap.add_argument("--template", default="template.txt")
    ap.add_argument("--out", default="out.csv")
    ap.add_argument("--optimizer", default="bootstrap", choices=["none","bootstrap","mipro","gepa"])
    args = ap.parse_args()

    configure_lm()
    template = open(args.template).read()
    wins_df = pd.read_csv(args.wins)
    trainset = build_trainset_from_wins(wins_df, template)
    program = compile_program(trainset, args.optimizer)
    leads_df = pd.read_csv(args.leads)
    out_df = generate_for_leads(program, leads_df, template)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {args.out} | rows={len(out_df)}")

if __name__ == "__main__":
    main()
