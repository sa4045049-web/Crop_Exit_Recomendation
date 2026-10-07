
from flask import Flask, render_template, request, jsonify
from pathlib import Path
import csv, math, statistics, random
from datetime import datetime

app = Flask(__name__)

CROPS = {
    "Wheat":   {"yield": 18, "cost": 42000, "base_price": 2450, "vol": 0.08, "days": 120, "storage": 2.2, "weather": 0.18},
    "Rice":    {"yield": 22, "cost": 48000, "base_price": 2350, "vol": 0.10, "days": 135, "storage": 2.5, "weather": 0.24},
    "Maize":   {"yield": 24, "cost": 39000, "base_price": 2200, "vol": 0.12, "days": 105, "storage": 1.8, "weather": 0.20},
    "Cotton":  {"yield": 8,  "cost": 52000, "base_price": 6900, "vol": 0.16, "days": 165, "storage": 3.0, "weather": 0.28},
    "Soybean": {"yield": 12, "cost": 41000, "base_price": 4900, "vol": 0.14, "days": 110, "storage": 2.0, "weather": 0.22},
    "Onion":   {"yield": 150,"cost": 65000, "base_price": 2400, "vol": 0.28, "days": 120, "storage": 4.0, "weather": 0.30},
    "Chickpea":{"yield": 11, "cost": 36000, "base_price": 5700, "vol": 0.13, "days": 115, "storage": 2.0, "weather": 0.17},
}

# Demo historical market data. Replace with verified mandi data for real deployment.
HISTORY = {
    "Wheat":   [2260,2310,2350,2390,2410,2440,2420,2460,2490,2510,2480,2450],
    "Rice":    [2180,2210,2260,2290,2320,2360,2400,2380,2350,2330,2310,2350],
    "Maize":   [2050,2080,2110,2160,2190,2220,2250,2280,2240,2210,2180,2200],
    "Cotton":  [6200,6350,6480,6600,6750,6880,7020,7150,7060,6950,6820,6900],
    "Soybean": [4300,4450,4520,4680,4750,4860,5010,5080,4970,4880,4820,4900],
    "Onion":   [1700,1900,2150,2500,2900,2700,2350,2100,1850,2200,2600,2400],
    "Chickpea":[5100,5250,5380,5500,5600,5750,5900,6000,5850,5700,5600,5700],
}

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def linear_slope(values):
    n = len(values)
    xbar = (n - 1) / 2
    ybar = sum(values) / n
    den = sum((i - xbar) ** 2 for i in range(n))
    if den == 0:
        return 0
    return sum((i - xbar) * (y - ybar) for i, y in enumerate(values)) / den

def forecast_prices(crop, months=3):
    hist = HISTORY[crop]
    slope = linear_slope(hist)
    last = hist[-1]
    # Mild mean reversion prevents unrealistic runaway forecasts.
    forecasts = []
    for m in range(1, months + 1):
        trend = last + slope * m
        seasonal = 1 + 0.012 * math.sin((len(hist) + m) * math.pi / 2)
        value = trend * seasonal
        forecasts.append(round(value, 2))
    return forecasts, slope

def risk_label(score):
    if score < 30: return "LOW"
    if score < 55: return "MEDIUM"
    if score < 75: return "HIGH"
    return "CRITICAL"

def analyze_crop(crop, area, current_price, days_left, rainfall_risk, temp_risk, cost_extra=0, storage_months=0):
    p = CROPS[crop]
    forecasts, slope = forecast_prices(crop, 3)
    future_price = forecasts[min(2, max(0, round(days_left / 30) - 1))]
    expected_yield = p["yield"]
    revenue_now = area * expected_yield * current_price
    total_cost = area * (p["cost"] + cost_extra)
    future_revenue = area * expected_yield * future_price
    storage_cost = area * expected_yield * p["storage"] * storage_months
    future_profit = future_revenue - total_cost - storage_cost
    now_profit = revenue_now - total_cost
    break_even = (total_cost + storage_cost) / max(area * expected_yield, 1)

    price_trend_pct = ((future_price - current_price) / max(current_price, 1)) * 100
    price_risk = clamp(abs(price_trend_pct) * 1.8 + p["vol"] * 35, 0, 100)
    weather_risk = clamp((rainfall_risk * 0.55 + temp_risk * 0.45) + p["weather"] * 35, 0, 100)
    margin_risk = clamp(50 - (future_profit / max(future_revenue, 1)) * 100, 0, 100)
    market_risk = clamp(p["vol"] * 100 + max(0, -price_trend_pct) * 1.5, 0, 100)

    risk = round(0.35 * market_risk + 0.25 * weather_risk + 0.25 * margin_risk + 0.15 * price_risk, 1)
    profit_margin = (future_profit / future_revenue * 100) if future_revenue else -100

    # Decision logic
    if future_profit < 0 and now_profit >= 0:
        decision = "SELL / EXIT EARLY"
    elif future_profit < 0:
        decision = "EXIT / CUT LOSS"
    elif risk >= 72:
        decision = "SELL / REVIEW NOW"
    elif price_trend_pct >= 5 and risk < 58:
        decision = "HOLD / WAIT"
    elif price_trend_pct >= 1 and profit_margin >= 12:
        decision = "HOLD"
    else:
        decision = "WAIT & MONITOR"

    confidence = round(clamp(92 - p["vol"] * 100 - abs(price_trend_pct) * 0.8 - risk * 0.18, 48, 91), 1)

    reasons = []
    if price_trend_pct >= 4:
        reasons.append(f"Model trend indicates about {price_trend_pct:.1f}% upside over the selected horizon.")
    elif price_trend_pct <= -4:
        reasons.append(f"Model trend indicates about {abs(price_trend_pct):.1f}% downside risk over the selected horizon.")
    else:
        reasons.append("Expected price movement is relatively flat, so timing is more important than chasing the market.")
    if future_profit > now_profit:
        reasons.append(f"Waiting could add approximately ₹{future_profit-now_profit:,.0f} to field-level profit before extra holding cost.")
    else:
        reasons.append(f"Selling now avoids an estimated ₹{now_profit-future_profit:,.0f} deterioration in profit.")
    if weather_risk >= 60:
        reasons.append("Weather stress is a significant part of the risk score.")
    if break_even > future_price:
        reasons.append("The projected price is below the break-even level after estimated costs.")
    else:
        reasons.append(f"Projected price remains above the break-even level of ₹{break_even:,.0f}/unit.")

    # What-if scenarios
    scenarios = []
    for label, price_factor, extra_days in [
        ("Sell now", 1.00, 0),
        ("Wait 1 month", 1.03, 30),
        ("Wait 3 months", 1.07, 90),
        ("Stress case", 0.90, 60),
    ]:
        sp = current_price * price_factor
        extra_storage = area * expected_yield * p["storage"] * max(0, extra_days / 30)
        rev = area * expected_yield * sp
        prof = rev - total_cost - extra_storage
        scenarios.append({"label": label, "price": round(sp), "profit": round(prof)})

    return {
        "crop": crop,
        "decision": decision,
        "confidence": confidence,
        "risk": risk,
        "risk_label": risk_label(risk),
        "current_price": round(current_price, 2),
        "forecast": forecasts,
        "future_price": round(future_price, 2),
        "price_trend_pct": round(price_trend_pct, 2),
        "area": area,
        "yield_per_acre": expected_yield,
        "revenue_now": round(revenue_now),
        "future_revenue": round(future_revenue),
        "total_cost": round(total_cost),
        "future_profit": round(future_profit),
        "now_profit": round(now_profit),
        "break_even": round(break_even, 2),
        "profit_margin": round(profit_margin, 1),
        "weather_risk": round(weather_risk, 1),
        "market_risk": round(market_risk, 1),
        "margin_risk": round(margin_risk, 1),
        "reasons": reasons,
        "scenarios": scenarios,
        "slope": round(slope, 2),
    }

@app.route("/")
def home():
    return render_template("index.html", crops=list(CROPS.keys()))

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    d = request.get_json(force=True)
    crop = d.get("crop", "Wheat")
    if crop not in CROPS:
        return jsonify({"error": "Unknown crop"}), 400
    try:
        area = float(d.get("area", 1))
        current_price = float(d.get("current_price", CROPS[crop]["base_price"]))
        days_left = int(d.get("days_left", 60))
        rainfall_risk = float(d.get("rainfall_risk", 30))
        temp_risk = float(d.get("temp_risk", 25))
        cost_extra = float(d.get("extra_cost", 0))
        storage_months = float(d.get("storage_months", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Please enter valid numeric values."}), 400

    if area <= 0 or current_price <= 0:
        return jsonify({"error": "Area and current price must be greater than zero."}), 400

    result = analyze_crop(crop, area, current_price, days_left, rainfall_risk, temp_risk, cost_extra, storage_months)
    return jsonify(result)

@app.route("/api/compare", methods=["POST"])
def api_compare():
    d = request.get_json(force=True)
    crops = d.get("crops", list(CROPS.keys())[:3])
    area = float(d.get("area", 1))
    for crop in crops:
        if crop not in CROPS:
            return jsonify({"error": f"Unknown crop: {crop}"}), 400
    out = []
    for crop in crops[:4]:
        current = float(d.get("prices", {}).get(crop, CROPS[crop]["base_price"]))
        out.append(analyze_crop(crop, area, current, 60, 30, 25))
    out.sort(key=lambda x: x["future_profit"], reverse=True)
    return jsonify(out)

@app.route("/api/crops")
def api_crops():
    return jsonify(CROPS)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
