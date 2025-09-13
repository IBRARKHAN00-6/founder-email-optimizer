# YC Email Optimizer (DSPy)

Give us your **3 best cold emails** and a **leads CSV**. Get back optimized, YC‑style outreach.

## Quickstart
```bash
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-...' > .env
python cli.py --wins wins.csv --leads leads.csv --template template.txt --out out.csv --optimizer bootstrap
```

## Inputs

- **wins.csv**: columns `subject`, `body` (more rows welcome)
- **leads.csv**: columns: `first_name`, `company` (+ optional `persona`, `pain`, `product`, `product_value`, `customer_example`, `impact_metric`, `sender_name`, `sender_role`)

## Output

- **out.csv**: adds `optimized_subject`, `optimized_body`, `score_0_10`, `feedback`

## Notes

Uses DSPy Signatures + Predict modules and BootstrapFewShot or MIPROv2 for optimization.

Default LM: `openai/gpt-4o-mini`. Override with env:

```bash
MODEL_ID=openai/gpt-4o-mini
API_BASE=http://localhost:7501/v1
OPENAI_API_KEY=...
```

## Risk checks & blind spots (called out)

- **Correlation to real replies**: the LLM judge is a proxy. Expect it to roughly enforce style/shape, not perfectly predict replies. Do a small **A/B** (1–2 weeks) to calibrate + auto‑tune rubric weights.
- **3 winners is sparse**: we compensate by bootstrapping demos + optimizing instructions. If they can provide 5–10, MIPROv2 tends to stabilize.
- **Hallucinated facts**: we keep slots explicit and penalize fluff; still add a simple regex whitelist for product names if needed.
- **Privacy/PII**: CSVs likely contain names; don't ship logs outside your network.

## Fast extensions

- `--variants 3 --pick best` (generate N and keep highest judge score)
- Clickbait guard: hard stop if subject contains spammy tokens
- Subject‑line policy: enforce presence of a concrete noun + numeric
- Persona presets: `--persona yc_founder` vs `--persona cio_enterprise`
- Cache control: set unique `rollout_id` when you want fresh generations

## Usage Examples

```bash
# Basic usage with bootstrap optimization
python cli.py

# Use MIPROv2 optimizer (stronger but slower)
python cli.py --optimizer mipro

# No optimization, just run the base pipeline
python cli.py --optimizer none

# Custom files
python cli.py --wins my_winners.csv --leads my_leads.csv --out results.csv
```
