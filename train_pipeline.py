"""
RentIQ — Standalone ML Training Pipeline
Run: python train_pipeline.py
Trains 4 models, saves best to best_model.pkl, prints metrics & comparison.
"""
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

CITY_BASE_RENT = {
    "Mumbai": 55000, "Delhi": 38000, "Bangalore": 32000, "Hyderabad": 24000,
    "Chennai": 22000, "Pune": 20000, "Kolkata": 16000, "Ahmedabad": 14000,
    "Jaipur": 12000, "Lucknow": 10000,
}

def generate_data(n=15000, seed=42):
    np.random.seed(seed)
    cities = list(CITY_BASE_RENT.keys())
    furns  = ["Unfurnished", "Semi-Furnished", "Furnished"]
    fmul   = {"Unfurnished": 1.0, "Semi-Furnished": 1.25, "Furnished": 1.5}
    rows   = []
    for _ in range(n):
        city     = np.random.choice(cities)
        area     = float(np.clip(np.random.lognormal(7, 0.5), 250, 10000))
        bhk      = int(np.random.choice([1,2,3,4], p=[.15,.45,.30,.10]))
        bath     = int(min(bhk + np.random.randint(-1, 2), 5))
        furn     = np.random.choice(furns, p=[.3,.45,.25])
        park     = bool(np.random.random() > .4)
        floor    = int(np.random.randint(0, 25))
        tfl      = int(max(floor, np.random.randint(4, 30)))
        age      = int(np.random.randint(0, 35))
        metro    = bool(np.random.random() > .55)
        gym      = bool(np.random.random() > .65)
        pool     = bool(np.random.random() > .80)
        sec      = bool(np.random.random() > .40)
        lift     = bool(np.random.random() > .45)
        balcony  = bool(np.random.random() > .50)
        base     = CITY_BASE_RENT[city]
        rent     = (base * .012 * area**.72 + bhk*.15*base + (bath-1)*.04*base*.1) * fmul[furn]
        rent    *= (1 + .07*metro + .06*gym + .09*pool + .04*sec + .03*lift
                      + .02*balcony + .03*park + (.05 if floor>5 else 0)
                      - (.08 if age>15 else 0) - (.15 if age>25 else 0))
        rent    *= np.random.lognormal(0, .08)
        rent     = max(round(rent/100)*100, 3000)
        rows.append({"city":city,"area":area,"bhk":bhk,"bathrooms":bath,"furnishing":furn,
                     "parking":int(park),"floor":floor,"total_floors":tfl,"building_age":age,
                     "near_metro":int(metro),"gym":int(gym),"pool":int(pool),"security":int(sec),
                     "lift":int(lift),"balcony":int(balcony),"rent":rent})
    return pd.DataFrame(rows)

def build_pipe(reg):
    num = ["area","bhk","bathrooms","floor","total_floors","building_age",
           "parking","near_metro","gym","pool","security","lift","balcony"]
    cat = ["city","furnishing"]
    prep = ColumnTransformer([
        ("num", StandardScaler(), num),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
    ])
    return Pipeline([("prep", prep), ("model", reg)])

def evaluate(pipe, X_test, y_test):
    y_pred = pipe.predict(X_test)
    return {
        "R²":   round(r2_score(y_test, y_pred), 4),
        "MAE":  f"₹{mean_absolute_error(y_test, y_pred):,.0f}",
        "RMSE": f"₹{np.sqrt(mean_squared_error(y_test, y_pred)):,.0f}",
    }

if __name__ == "__main__":
    print("⚙️  Generating training data…")
    df = generate_data(15000)
    X  = df.drop("rent", axis=1)
    y  = df["rent"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42)

    models = {
        "Random Forest":    RandomForestRegressor(n_estimators=150, max_depth=14, random_state=42, n_jobs=-1),
        "Linear Regression": LinearRegression(),
        "Neural Network":   MLPRegressor(hidden_layer_sizes=(128,64,32), max_iter=500, random_state=42),
    }
    try:
        from xgboost import XGBRegressor
        models["XGBoost"] = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=.1, random_state=42, verbosity=0)
    except ImportError:
        print("⚠️  XGBoost not installed — skipping")

    best_r2   = -np.inf
    best_name = ""
    results   = {}

    print("\n🏋️  Training models…\n")
    for name, reg in models.items():
        pipe = build_pipe(reg)
        pipe.fit(X_train, y_train)
        metrics       = evaluate(pipe, X_test, y_test)
        results[name] = metrics
        r2_val        = float(metrics["R²"])
        print(f"  {name:<22} R²={metrics['R²']}  MAE={metrics['MAE']}  RMSE={metrics['RMSE']}")
        if r2_val > best_r2:
            best_r2   = r2_val
            best_name = name
            best_pipe = pipe

    # Save
    joblib.dump(best_pipe, "best_model.pkl")
    print(f"\n✅  Best model: {best_name} (R²={best_r2:.4f}) — saved to best_model.pkl")

    # Feature importance (Random Forest only)
    if "Random Forest" in models:
        rf_pipe = build_pipe(models["Random Forest"])
        rf_pipe.fit(X_train, y_train)
        feature_names = (
            X_train.select_dtypes(exclude="object").columns.tolist()
            + rf_pipe.named_steps["prep"].named_transformers_["cat"].get_feature_names_out(["city","furnishing"]).tolist()
        )
        importances = rf_pipe.named_steps["model"].feature_importances_
        top10 = sorted(zip(feature_names, importances), key=lambda x:-x[1])[:10]
        print("\n📊  Top-10 Feature Importances (Random Forest):")
        for feat, imp in top10:
            bar = "█" * int(imp * 200)
            print(f"  {feat:<30} {imp:.4f}  {bar}")

    print("\n🚀  Training complete. Run rentiq_backend.py to start the API server.")
