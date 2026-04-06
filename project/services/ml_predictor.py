"""
ML Price Predictor using RandomForestRegressor.
Features: crop_name (encoded), season (encoded), year, district (encoded), demand_index
Target: price_per_quintal
"""
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from config import Config


_le_crop = LabelEncoder()
_le_season = LabelEncoder()
_le_district = LabelEncoder()

_model = None
_scaler = None
_trained = False


def _normalize_label(value):
    return str(value or "").strip().lower()


def _safe_transform(encoder, value):
    classes = list(getattr(encoder, "classes_", []))
    if not classes:
        raise ValueError("Encoder has not been trained.")

    label = str(value or "").strip()
    if label in classes:
        return int(encoder.transform([label])[0])

    normalized = { _normalize_label(item): item for item in classes }
    matched = normalized.get(_normalize_label(label))
    if matched:
        return int(encoder.transform([matched])[0])

    return int(encoder.transform([classes[0]])[0])


def _encode_features(df):
    df = df.copy()
    df["crop_enc"] = df["crop_name"].apply(lambda value: _safe_transform(_le_crop, value))
    df["season_enc"] = df["season"].apply(lambda value: _safe_transform(_le_season, value))
    df["district_enc"] = df["district"].apply(lambda value: _safe_transform(_le_district, value))
    df["demand_index"] = df["demand_index"].fillna(1.0)
    return df[["crop_enc", "season_enc", "year", "district_enc", "demand_index"]]


def train_model(db):
    """Train the ML model on price_history data and persist it."""
    global _model, _scaler, _trained

    from models.price_history import PriceHistory

    df = PriceHistory.get_all_as_df(db)
    if df.empty or len(df) < 20:
        return False, "Not enough data to train model."

    df = df[df["crop_name"].isin(Config.CROPS)].copy()
    df = df[df["season"].isin(Config.SEASONS)].copy()
    df = df[df["district"].notna()].copy()
    df["district"] = df["district"].astype(str).str.strip()
    df = df[df["district"] != ""]
    df["demand_index"] = df["demand_index"].fillna(1.0)

    if df.empty or df["district"].nunique() == 0:
        return False, "No valid district data found for training."

    _le_crop.fit(sorted(df["crop_name"].unique()))
    _le_season.fit(sorted(df["season"].unique()))
    _le_district.fit(sorted(df["district"].unique()))

    X = _encode_features(df)
    y = df["price_per_quintal"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    _scaler = StandardScaler()
    X_train_s = _scaler.fit_transform(X_train)
    X_test_s = _scaler.transform(X_test)

    _model = RandomForestRegressor(
        n_estimators=150, max_depth=10, random_state=42, n_jobs=1
    )
    _model.fit(X_train_s, y_train)

    preds = _model.predict(X_test_s)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    try:
        joblib.dump(_model, Config.MODEL_PATH)
        joblib.dump(_scaler, Config.SCALER_PATH)
        joblib.dump(
            {
                "le_crop": _le_crop,
                "le_season": _le_season,
                "le_district": _le_district,
            },
            Config.MODEL_PATH + ".encoders",
        )
    except Exception:
        # Keep the in-memory model available even if file persistence is blocked.
        pass

    _trained = True
    return True, f"Model trained. MAE=Rs {mae:.0f}, R2={r2:.3f}"


def _load_model_if_needed():
    global _model, _scaler, _trained, _le_crop, _le_season, _le_district
    if _trained:
        return True
    if os.path.exists(Config.MODEL_PATH) and os.path.exists(Config.SCALER_PATH):
        _model = joblib.load(Config.MODEL_PATH)
        _scaler = joblib.load(Config.SCALER_PATH)
        encoders = joblib.load(Config.MODEL_PATH + ".encoders")
        _le_crop = encoders["le_crop"]
        _le_season = encoders["le_season"]
        _le_district = encoders["le_district"]
        _trained = True
        return True
    return False


def predict_price(crop_name, season, year, district="Guntur", demand_index=1.0):
    """Predict price for a given crop/season/year/district."""
    if not _load_model_if_needed():
        return None, "Model not trained yet."
    try:
        row = pd.DataFrame(
            [
                {
                    "crop_name": crop_name,
                    "season": season,
                    "year": year,
                    "district": district,
                    "demand_index": demand_index,
                }
            ]
        )
        X = _encode_features(row)
        X_s = _scaler.transform(X)
        price = _model.predict(X_s)[0]
        return round(float(price), 2), None
    except Exception as exc:
        return None, str(exc)


def predict_all_crops(season, year, district="Guntur"):
    """Predict prices for all supported crops."""
    results = {}
    for crop in Config.CROPS:
        price, err = predict_price(crop, season, year, district)
        results[crop] = {"price": price, "error": err}
    return results


def get_price_trend(db, crop_name, district="Guntur"):
    """Returns historical + predicted prices for a crop."""
    from models.price_history import PriceHistory

    rows = PriceHistory.get_for_crop(db, crop_name, district)

    historical = {}
    for row in rows:
        key = f"{row[2]}-{row[3]}"
        historical[key] = row[6]

    import datetime

    current_year = datetime.datetime.now().year
    predictions = []
    for yr in range(current_year, current_year + 3):
        for season in Config.SEASONS:
            price, err = predict_price(crop_name, season, yr, district)
            if price is not None and not err:
                predictions.append(
                    {"year": yr, "season": season, "price": price, "predicted": True}
                )

    return historical, predictions
