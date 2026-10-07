
# CropExit Intelligence — Ready-to-Build PC Prototype

## What this project does

CropExit Intelligence is an academic prototype for **crop exit / sell / hold decision support**.

Instead of only answering “Which crop should I grow?”, it answers:

- Should I sell now?
- Should I hold and wait?
- Is the expected future price worth the waiting cost?
- What is my break-even price?
- What profit can I expect?
- How much does weather risk change the decision?
- What happens under sell-now, wait, and stress-case scenarios?
- Which crop is economically stronger for the same land area?

## Advanced features

1. AI-style multi-factor decision engine
2. Future market-price trend forecast
3. Revenue and future-profit simulator
4. Break-even price calculation
5. Exit-window / hold-vs-sell decision
6. Weather-risk score
7. Market-volatility score
8. Margin-risk score
9. Explainable AI reasons
10. What-if simulator
11. Crop comparator
12. Risk-adjusted decision confidence
13. Storage/holding-cost effect
14. Professional responsive dashboard
15. No voice assistant
16. No paid API keys required
17. Works locally without an internet/API dependency for the dashboard chart

## Important academic limitation

The bundled market history is synthetic demonstration data. It is included so the prototype can run completely on a PC without API keys.

For real deployment, replace `HISTORY` in `app.py` with verified mandi/market data and validate the model with real historical datasets. Do not present the demo forecasts as real market predictions.

## Windows / VS Code setup

Use Python 3.11 or 3.12 if possible.

1. Extract this ZIP.
2. Open the extracted folder in VS Code.
3. Open Terminal.
4. Run:

```text
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

5. Open:

```text
http://127.0.0.1:5000
```

If `py` does not work, try:

```text
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

## Project flow

User inputs:
Crop + land area + current price + days left + weather risk + extra cost + storage time

↓

Decision Engine:
Market trend + price volatility + weather risk + margin + holding cost

↓

Outputs:
HOLD / WAIT / SELL / EXIT

↓

Explainable result:
Future price + revenue + profit + break-even + risk + confidence

↓

Decision simulator:
Sell now vs wait vs stress case

↓

Crop comparator:
Compare multiple crops on the same land

## Suggested viva line

“Most agriculture systems stop at crop recommendation, weather or market information. Our prototype adds an economic exit-decision layer. It estimates the break-even price, future profit, holding cost and risk, then compares alternative actions such as sell now, hold, wait or exit early and explains why.”
