
import json
import os
import argparse
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# -----------------------
# 1) synthetic data generator (simple)
# -----------------------
def generate_synthetic_data(n=5000, seed=42) -> pd.DataFrame:
    np.random.seed(seed)
    CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad", "Jaipur"]
    FURNISH = ["Unfurnished", "Semi-Furnished", "Fully-Furnished"]
    PARKING = ["None", "Two-Wheeler", "Four-Wheeler", "Both"]

    city = np.random.choice(CITIES, size=n)
    area_sqft = np.random.randint(300, 3500, size=n)
    bhk = np.random.randint(1, 6, size=n)
    bathrooms = np.clip(bhk + np.random.randint(-1, 2, size=n), 1, 6)
    furnishing = np.random.choice(FURNISH, size=n, p=[0.45, 0.35, 0.2])
    parking = np.random.choice(PARKING, size=n, p=[0.35, 0.35, 0.2, 0.1])
    floor = np.random.randint(0, 30, size=n)
    total_floors = np.clip(floor + np.random.randint(1, 10, size=n), 1, 35)
    age_years = np.random.randint(0, 30, size=n)
    near_metro = np.random.choice([0, 1], size=n, p=[0.6, 0.4])

    city_inflation = {
        "Mumbai": 1.4, "Delhi": 1.25, "Bengaluru": 1.35, "Hyderabad": 1.15,
        "Chennai": 1.10, "Pune": 1.20, "Kolkata": 0.95, "Ahmedabad": 0.9, "Jaipur": 0.85
    }

    base = 6_000 + area_sqft * 18 + bhk * 3_000 + bathrooms * 1_200
    base = base + near_metro * 5_000 + (total_floors - floor) * 100
    base = base * np.array([city_inflation[c] for c in city])
    furnish_factor = {"Unfurnished": 0.95, "Semi-Furnished": 1.0, "Fully-Furnished": 1.08}
    parking_bonus = {"None": 0.96, "Two-Wheeler": 1.0, "Four-Wheeler": 1.04, "Both": 1.07}
    base = base * np.array([furnish_factor[f] for f in furnishing])
    base = base * np.array([parking_bonus[p] for p in parking])
    age_discount = (1 - (age_years / 100) * 0.25)  # small discount with age
    base = base * age_discount
    noise = np.random.normal(0, 5000, size=n)
    rent = np.clip(base + noise, 3000, None).astype(int)

    df = pd.DataFrame({
        "city": city,
        "area_sqft": area_sqft,
        "bhk": bhk,
        "bathrooms": bathrooms,
        "furnishing": furnishing,
        "parking": parking,
        "floor": floor,
        "total_floors": total_floors,
        "age_years": age_years,
        "near_metro": near_metro,
        "rent_inr": rent
    })
    return df

# -----------------------
# 2) build pipeline
# -----------------------
def build_pipeline(categorical_features, numeric_features):
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse=False), categorical_features),
            ("num", StandardScaler(), numeric_features),
        ]
    )

    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    pipe = Pipeline([("preprocess", preprocessor), ("model", model)])
    return pipe

# -----------------------
# 3) train & eval
# -----------------------
def train_and_evaluate(df: pd.DataFrame, out_path: str = "app/model.joblib", test_size=0.2, random_state=42):
    target = "rent_inr"
    features = [c for c in df.columns if c != target]
    X = df[features]
    y = df[target]

    # detect categorical / numeric
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    num_cols = X.select_dtypes(exclude=["object"]).columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    pipe = build_pipeline(categorical_features=cat_cols, numeric_features=num_cols)
    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    # bundle artifacts
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    joblib.dump({"pipeline": pipe, "features": features, "mae": mae, "r2": r2}, out_path)

    print(f"Trained model saved to: {out_path}")
    print(f"MAE: {mae:,.2f} INR\tR2: {r2:.4f}")
    return out_path

# -----------------------
# 4) prediction helper
# -----------------------
class RentPredictor:
    def __init__(self, model_path="app/model.joblib"):
        bundle = joblib.load(model_path)
        self.pipe = bundle["pipeline"]
        self.features = bundle["features"]
        self.mae = bundle.get("mae", None)
        self.r2 = bundle.get("r2", None)

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: dict with same features used in training
        returns: dict with predicted_rent and optionally model metrics
        """
        # build DataFrame in the training order; missing columns will raise KeyError
        df = pd.DataFrame([payload])[self.features]
        pred = float(self.pipe.predict(df)[0])
        return {
            "predicted_rent_inr": int(max(pred, 0)),
            "model_mae_inr": float(self.mae) if self.mae is not None else None,
            "model_r2": float(self.r2) if self.r2 is not None else None
        }

# -----------------------
# 5) CLI entrypoint
# -----------------------
def main():
    parser = argparse.ArgumentParser(description="House Rent Prediction training & quick predict")
    parser.add_argument("--train", action="store_true", help="Train model (uses synthetic data if no input file provided)")
    parser.add_argument("--data", type=str, default=None, help="Optional CSV data path (must have same columns)")
    parser.add_argument("--out", type=str, default="app/model.joblib", help="Output model filepath")
    parser.add_argument("--predict", type=str, default=None,
                        help="JSON string for a single sample to predict (must be used after training or you must have an existing model)")
    parser.add_argument("--generate", action="store_true", help="Generate synthetic CSV data to data/house_rent_synthetic.csv")
    args = parser.parse_args()

    if args.generate:
        os.makedirs("data", exist_ok=True)
        df = generate_synthetic_data(n=5000)
        df.to_csv("data/house_rent_synthetic.csv", index=False)
        print("Wrote data/house_rent_synthetic.csv", df.shape)

    if args.train:
        if args.data:
            df = pd.read_csv(args.data)
        else:
            print("No data path provided — generating synthetic data for training.")
            df = generate_synthetic_data(n=5000)
        train_and_evaluate(df, out_path=args.out)

    if args.predict:
        # try to ensure model exists
        if not os.path.exists(args.out):
            raise FileNotFoundError(f"Model not found at {args.out}. Train first or point --out to an existing model.")
        payload = json.loads(args.predict)
        predictor = RentPredictor(model_path=args.out)
        result = predictor.predict(payload)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
