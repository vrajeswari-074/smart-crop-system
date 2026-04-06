"""
Crop recommendation engine.
Combines:
  - Over-cultivation detection (avoid over-cultivated crops)
  - ML price prediction (prefer high-price crops)
  - Seasonal crop suitability
  - Demand/supply balancing for village-level suggestions
"""
import datetime

from config import Config
from services.analysis import detect_over_cultivation, get_crop_distribution
from services.ml_predictor import predict_all_crops


SEASON_CROPS = {
    "Kharif": ["Rice", "Maize", "Cotton", "Soybean", "Tomato", "Sugarcane"],
    "Rabi": ["Wheat", "Barley", "Potato", "Onion", "Sugarcane"],
    "Zaid": ["Maize", "Tomato", "Onion", "Potato"],
    "Annual": [
        "Sugarcane",
        "Cotton",
        "Wheat",
        "Rice",
        "Maize",
        "Tomato",
        "Onion",
        "Potato",
        "Soybean",
        "Barley",
    ],
}


CROP_INFO = {
    "Wheat": {
        "water": "Medium",
        "duration": "120 days",
        "icon": "W",
        "soil": ["Alluvial", "Black", "Red"],
        "yield_per_acre": 14.0,
    },
    "Rice": {
        "water": "High",
        "duration": "130 days",
        "icon": "R",
        "soil": ["Alluvial", "Black"],
        "yield_per_acre": 22.0,
    },
    "Maize": {
        "water": "Medium",
        "duration": "90 days",
        "icon": "M",
        "soil": ["Red", "Alluvial", "Laterite"],
        "yield_per_acre": 18.0,
    },
    "Tomato": {
        "water": "Medium",
        "duration": "70 days",
        "icon": "T",
        "soil": ["Red", "Alluvial"],
        "yield_per_acre": 120.0,
    },
    "Onion": {
        "water": "Low",
        "duration": "100 days",
        "icon": "O",
        "soil": ["Red", "Sandy"],
        "yield_per_acre": 65.0,
    },
    "Potato": {
        "water": "Medium",
        "duration": "80 days",
        "icon": "P",
        "soil": ["Alluvial", "Sandy"],
        "yield_per_acre": 85.0,
    },
    "Cotton": {
        "water": "Low",
        "duration": "160 days",
        "icon": "C",
        "soil": ["Black", "Red"],
        "yield_per_acre": 8.0,
    },
    "Soybean": {
        "water": "Low",
        "duration": "100 days",
        "icon": "S",
        "soil": ["Black", "Alluvial"],
        "yield_per_acre": 10.0,
    },
    "Sugarcane": {
        "water": "High",
        "duration": "300 days",
        "icon": "SC",
        "soil": ["Alluvial", "Black"],
        "yield_per_acre": 300.0,
    },
    "Barley": {
        "water": "Low",
        "duration": "110 days",
        "icon": "B",
        "soil": ["Sandy", "Red"],
        "yield_per_acre": 12.0,
    },
}


def get_recommendations(db, village, season, district, soil_type, water_avail):
    """
    Returns crop recommendations for temporary user inputs without saving data.
    The top 1-2 suggestions prioritize crops with lower oversupply risk.
    """
    year = datetime.datetime.now().year

    distribution = get_crop_distribution(db, village, season, year)
    flagged = detect_over_cultivation(distribution) if distribution else []
    overcultivated_crops = {f["crop"] for f in flagged if f["over_cultivated"]}
    crop_risks = {f["crop"]: f["risk_level"] for f in flagged}

    price_preds = predict_all_crops(season, year, district)
    demand_map = _get_demand_index_map(db, district, year)
    suitable_crops = SEASON_CROPS.get(season, Config.CROPS)

    prices = [v["price"] for v in price_preds.values() if v.get("price")]
    max_price = max(prices) if prices else 1
    min_price = min(prices) if prices else 0

    recommendations = []
    for crop in suitable_crops:
        pred = price_preds.get(crop, {})
        price = pred.get("price")
        if not price:
            continue

        info = CROP_INFO.get(crop, {})
        if not _matches_environment(info, soil_type, water_avail):
            continue

        is_overcultivated = crop in overcultivated_crops
        risk = crop_risks.get(crop, "Low Risk")
        demand_index = demand_map.get(crop, 1.0)

        price_score = (
            ((price - min_price) / (max_price - min_price + 1)) * 55
            if max_price > min_price
            else 27.5
        )
        diversity_bonus = 0 if is_overcultivated else 25
        demand_bonus = max(0, min(20, (demand_index - 0.9) * 50))
        score = price_score + diversity_bonus + demand_bonus

        recommendations.append(
            {
                "crop": crop,
                "predicted_price": price,
                "price_formatted": f"Rs {price:,.0f}",
                "is_overcultivated": is_overcultivated,
                "risk": risk,
                "risk_class": _risk_class(risk),
                "score": round(score, 1),
                "demand_index": round(demand_index, 2),
                "water_need": info.get("water", "Medium"),
                "duration": info.get("duration", "N/A"),
                "icon": info.get("icon", crop[:1].upper()),
                "yield_per_acre": info.get("yield_per_acre", 10.0),
                "why": _build_reason_labels(is_overcultivated, demand_index, risk),
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    risk_crops = [item for item in recommendations if item["is_overcultivated"]]
    alternatives = [item for item in recommendations if not item["is_overcultivated"]]
    best_choices = alternatives[:2] if alternatives else recommendations[:2]

    return {
        "risk_crops": risk_crops,
        "alternatives": alternatives,
        "best_choices": best_choices,
    }


def _matches_environment(info, soil_type, water_avail):
    water_req = info.get("water", "Medium")
    soil_pref = info.get("soil", [])

    if water_avail == "High":
        water_match = True
    elif water_avail == "Medium":
        water_match = water_req in ["Medium", "Low"]
    else:
        water_match = water_req == "Low"

    return water_match and soil_type in soil_pref


def _get_demand_index_map(db, district, year):
    rows = db.execute(
        """
        SELECT crop_name, AVG(demand_index)
        FROM price_history
        WHERE district = ? AND year >= ?
        GROUP BY crop_name
        """,
        (district, year - 3),
    ).fetchall()

    if not rows:
        rows = db.execute(
            "SELECT crop_name, AVG(demand_index) FROM price_history GROUP BY crop_name"
        ).fetchall()

    return {row[0]: row[1] for row in rows}


def _build_reason_labels(is_overcultivated, demand_index, risk):
    reasons = []

    if not is_overcultivated:
        reasons.append("Low village oversupply risk")
    if demand_index >= 1.1:
        reasons.append("Strong district demand")
    elif demand_index >= 1.0:
        reasons.append("Healthy market demand")
    if risk == "Low Risk":
        reasons.append("Good diversification choice")

    return reasons[:3]


def _risk_class(risk):
    if risk == "High Risk":
        return "danger"
    if risk == "Medium Risk":
        return "warning"
    return "success"
