"""
RentIQ - AI-Powered House Rent Prediction Backend
FastAPI + scikit-learn + MongoDB Atlas + Claude API
"""

# ─── requirements.txt ─────────────────────────────────────────────
# fastapi==0.111.0
# uvicorn[standard]==0.29.0
# scikit-learn==1.4.2
# xgboost==2.0.3
# pandas==2.2.2
# numpy==1.26.4
# joblib==1.4.2
# pymongo==4.7.2
# motor==3.4.0          # async MongoDB
# python-jose[cryptography]==3.3.0
# passlib[bcrypt]==1.7.4
# python-multipart==0.0.9
# pydantic==2.7.1
# anthropic==0.26.0
# python-dotenv==1.0.1
# slowapi==0.1.9        # rate limiting
# httpx==0.27.0

import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

import numpy as np
import pandas as pd
import joblib
from dotenv import load_dotenv

# FastAPI
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

# Auth
from passlib.context import CryptContext
from jose import JWTError, jwt

# MongoDB (async)
from motor.motor_asyncio import AsyncIOMotorClient

# ML
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Anthropic
import anthropic

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────
SECRET_KEY        = os.getenv("SECRET_KEY", "rentiq-super-secret-key-change-in-prod")
ALGORITHM         = "HS256"
ACCESS_TOKEN_MINS = 60 * 24  # 24 hours
MONGO_URI         = os.getenv("MONGO_URI", "mongodb://localhost:27017")
CLAUDE_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
DB_NAME           = "rentiq"

# ─── App setup ────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="RentIQ API", version="1.0.0", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://rentiq.vercel.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# ─── DB ───────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.db = app.mongodb_client[DB_NAME]
    await train_all_models()

@app.on_event("shutdown")
async def shutdown():
    app.mongodb_client.close()

def get_db(request: Request):
    return request.app.db

# ─── Auth ─────────────────────────────────────────────────────────
pwd_ctx    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2     = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2), db=Depends(get_db)):
    creds_exc = HTTPException(status_code=401, detail="Could not validate credentials",
                              headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise creds_exc
    except JWTError:
        raise creds_exc
    user = await db["users"].find_one({"email": email})
    if not user:
        raise creds_exc
    return user

# ─── Pydantic Models ──────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PredictionInput(BaseModel):
    city: str
    locality: Optional[str] = ""
    area: float = Field(..., gt=50, lt=50000, description="Area in sqft")
    bhk: int = Field(..., ge=1, le=10)
    bathrooms: int = Field(1, ge=1, le=10)
    furnishing: str = "Unfurnished"  # Unfurnished | Semi-Furnished | Furnished
    parking: bool = False
    floor: int = 0
    total_floors: int = Field(1, ge=1)
    building_age: int = Field(0, ge=0, le=100)
    near_metro: bool = False
    gym: bool = False
    pool: bool = False
    security: bool = False
    lift: bool = False
    balcony: bool = False

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# ─── ML Pipeline ──────────────────────────────────────────────────
MODELS: dict = {}
MODEL_METRICS: dict = {}

CITY_BASE_RENT = {
    "Mumbai": 55000, "Delhi": 38000, "Bangalore": 32000, "Hyderabad": 24000,
    "Chennai": 22000, "Pune": 20000, "Kolkata": 16000, "Ahmedabad": 14000,
    "Jaipur": 12000, "Lucknow": 10000,
}

def generate_synthetic_data(n=10000) -> pd.DataFrame:
    """Generate realistic synthetic Indian rental data for training."""
    np.random.seed(42)
    cities   = list(CITY_BASE_RENT.keys())
    furns    = ["Unfurnished", "Semi-Furnished", "Furnished"]
    furn_mul = {"Unfurnished": 1.0, "Semi-Furnished": 1.25, "Furnished": 1.5}

    rows = []
    for _ in range(n):
        city         = np.random.choice(cities)
        area         = np.random.lognormal(mean=7, sigma=0.5)
        area         = float(np.clip(area, 250, 10000))
        bhk          = int(np.clip(np.random.choice([1,2,3,4], p=[.15,.45,.30,.10]), 1, 4))
        bathrooms    = int(min(bhk + np.random.randint(-1, 2), 5))
        furnishing   = np.random.choice(furns, p=[.3, .45, .25])
        parking      = bool(np.random.random() > 0.4)
        floor        = int(np.random.randint(0, 25))
        total_floors = int(max(floor, np.random.randint(4, 30)))
        building_age = int(np.random.randint(0, 35))
        near_metro   = bool(np.random.random() > 0.55)
        gym   = bool(np.random.random() > 0.65)
        pool  = bool(np.random.random() > 0.8)
        sec   = bool(np.random.random() > 0.4)
        lift  = bool(np.random.random() > 0.45)
        balcony = bool(np.random.random() > 0.5)

        base = CITY_BASE_RENT[city]
        rent = (
            base * 0.012 * area ** 0.72
            + bhk * 0.15 * base
            + (bathrooms - 1) * 0.04 * base * 0.1
        ) * furn_mul[furnishing]
        rent *= (1 + 0.07 * near_metro + 0.06 * gym + 0.09 * pool
                   + 0.04 * sec + 0.03 * lift + 0.02 * balcony
                   + 0.03 * parking + (0.05 if floor > 5 else 0)
                   - (0.08 if building_age > 15 else 0)
                   - (0.15 if building_age > 25 else 0))
        rent *= np.random.lognormal(0, 0.08)  # noise
        rent = max(round(rent / 100) * 100, 3000)
        rows.append({
            "city": city, "area": area, "bhk": bhk, "bathrooms": bathrooms,
            "furnishing": furnishing, "parking": int(parking), "floor": floor,
            "total_floors": total_floors, "building_age": building_age,
            "near_metro": int(near_metro), "gym": int(gym), "pool": int(pool),
            "security": int(sec), "lift": int(lift), "balcony": int(balcony), "rent": rent,
        })
    return pd.DataFrame(rows)

def build_pipeline(regressor) -> Pipeline:
    cat_features = ["city", "furnishing"]
    num_features = ["area","bhk","bathrooms","floor","total_floors","building_age",
                    "parking","near_metro","gym","pool","security","lift","balcony"]
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features),
    ])
    return Pipeline([("preprocessor", preprocessor), ("model", regressor)])

async def train_all_models():
    """Train all ML models on startup (runs in thread to not block event loop)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _train_sync)

def _train_sync():
    df = generate_synthetic_data(12000)
    X = df.drop("rent", axis=1)
    y = df["rent"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model_defs = {
        "random_forest": RandomForestRegressor(n_estimators=120, max_depth=14, random_state=42, n_jobs=-1),
        "linear_regression": LinearRegression(),
        "neural_network": MLPRegressor(hidden_layer_sizes=(128, 64, 32), max_iter=400,
                                        activation="relu", solver="adam", random_state=42),
    }

    # XGBoost optional
    try:
        from xgboost import XGBRegressor
        model_defs["xgboost"] = XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.1,
                                               random_state=42, verbosity=0)
    except ImportError:
        pass

    for name, reg in model_defs.items():
        pipe = build_pipeline(reg)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        mae  = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2   = float(r2_score(y_test, y_pred))
        MODELS[name] = pipe
        MODEL_METRICS[name] = {"mae": round(mae, 2), "rmse": round(rmse, 2),
                                "r2": round(r2, 4), "accuracy": round(r2 * 100, 2)}
        print(f"[RentIQ] {name}: R²={r2:.3f} MAE=₹{mae:,.0f} RMSE=₹{rmse:,.0f}")

    # Save best model
    if MODELS:
        best = max(MODEL_METRICS, key=lambda k: MODEL_METRICS[k]["r2"])
        joblib.dump(MODELS[best], "best_model.pkl")
        print(f"[RentIQ] Best model: {best} → saved as best_model.pkl")

def prediction_to_dict(inp: PredictionInput, model_name="random_forest") -> dict:
    model = MODELS.get(model_name) or list(MODELS.values())[0] if MODELS else None
    if not model:
        raise HTTPException(status_code=503, detail="Models not trained yet.")
    row = pd.DataFrame([{
        "city": inp.city, "area": inp.area, "bhk": inp.bhk, "bathrooms": inp.bathrooms,
        "furnishing": inp.furnishing, "parking": int(inp.parking), "floor": inp.floor,
        "total_floors": inp.total_floors, "building_age": inp.building_age,
        "near_metro": int(inp.near_metro), "gym": int(inp.gym), "pool": int(inp.pool),
        "security": int(inp.security), "lift": int(inp.lift), "balcony": int(inp.balcony),
    }])
    predicted = float(model.predict(row)[0])
    predicted = round(predicted / 100) * 100
    # Ensemble uncertainty estimate
    preds = [round(float(m.predict(row)[0]) / 100) * 100 for m in MODELS.values()]
    low  = round(min(preds) * 0.93 / 100) * 100
    high = round(max(preds) * 1.07 / 100) * 100
    std  = float(np.std(preds))
    confidence = min(96, max(70, 100 - (std / predicted) * 100))
    city_avg = CITY_BASE_RENT.get(inp.city, 20000)
    percentile = min(95, max(10, 40 + (predicted - city_avg) / city_avg * 60))
    return {
        "predicted": predicted, "low": low, "high": high,
        "confidence": round(confidence, 1), "per_sqft": round(predicted / inp.area, 1),
        "percentile": round(percentile, 1), "model_used": model_name,
    }

# ─── Routes ───────────────────────────────────────────────────────

# --- Auth ---
@app.post("/register", tags=["auth"])
async def register(data: UserRegister, db=Depends(get_db)):
    if await db["users"].find_one({"email": data.email}):
        raise HTTPException(409, "Email already registered")
    user = {"_id": str(uuid.uuid4()), "name": data.name, "email": data.email,
            "password": hash_password(data.password), "created_at": datetime.utcnow()}
    await db["users"].insert_one(user)
    token = create_token({"sub": data.email})
    return {"access_token": token, "token_type": "bearer", "user": {"name": data.name, "email": data.email}}

@app.post("/login", response_model=Token, tags=["auth"])
async def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await db["users"].find_one({"email": form.username})
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token({"sub": user["email"]}), "token_type": "bearer"}

@app.get("/me", tags=["auth"])
async def me(user=Depends(get_current_user)):
    return {"name": user["name"], "email": user["email"], "created_at": str(user.get("created_at", ""))}

# --- Prediction ---
@app.post("/predict", tags=["predict"])
@limiter.limit("30/minute")
async def predict(request: Request, inp: PredictionInput,
                  db=Depends(get_db), user=Depends(get_current_user)):
    result = prediction_to_dict(inp)
    record = {
        "_id": str(uuid.uuid4()), "user_id": user["_id"],
        "input": inp.model_dump(), "result": result,
        "timestamp": datetime.utcnow(),
    }
    await db["predictions"].insert_one(record)
    return result

@app.post("/predict/guest", tags=["predict"])
@limiter.limit("10/minute")
async def predict_guest(request: Request, inp: PredictionInput):
    """Unauthenticated prediction (limited)."""
    return prediction_to_dict(inp)

# --- History & Analytics ---
@app.get("/history", tags=["history"])
async def history(db=Depends(get_db), user=Depends(get_current_user),
                  limit: int = 20, skip: int = 0):
    cursor = db["predictions"].find({"user_id": user["_id"]},
                                    sort=[("timestamp", -1)]).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"predictions": docs, "total": await db["predictions"].count_documents({"user_id": user["_id"]})}

@app.get("/analytics", tags=["analytics"])
async def analytics(db=Depends(get_db), user=Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": "$input.city", "count": {"$sum": 1},
                    "avg_rent": {"$avg": "$result.predicted"}}},
        {"$sort": {"count": -1}},
    ]
    city_stats = await db["predictions"].aggregate(pipeline).to_list(length=20)
    total = await db["predictions"].count_documents({"user_id": user["_id"]})
    return {"total_predictions": total, "city_breakdown": city_stats, "model_metrics": MODEL_METRICS}

# --- ML Models ---
@app.get("/models", tags=["ml"])
async def get_models():
    return {"models": MODEL_METRICS, "available": list(MODELS.keys())}

@app.post("/train", tags=["ml"])
async def retrain(user=Depends(get_current_user)):
    """Retrain models (admin only in production)."""
    await train_all_models()
    return {"status": "Training complete", "metrics": MODEL_METRICS}

# --- AI Chat ---
@app.post("/chat", tags=["ai"])
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest, user=Depends(get_current_user),
               db=Depends(get_db)):
    if not CLAUDE_API_KEY:
        raise HTTPException(503, "AI service not configured")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    system = (
        "You are RentIQ AI, a smart real estate assistant for Indian rental markets. "
        "Help with: rent estimation, market trends, investment advice, tenant rights, "
        "landlord guidance, locality recommendations, budget planning. "
        "Be concise, helpful, and use ₹ for prices. Keep responses under 200 words."
    )
    messages = [{"role": m.role, "content": m.content} for m in body.messages[-12:]]
    response = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=500, system=system, messages=messages
    )
    reply = response.content[0].text

    # Save to DB
    await db["chat_history"].insert_one({
        "_id": str(uuid.uuid4()), "user_id": user["_id"],
        "messages": [m.model_dump() for m in body.messages] + [{"role":"assistant","content":reply}],
        "timestamp": datetime.utcnow(),
    })
    return {"reply": reply}

# --- Market Data ---
@app.get("/market/{city}", tags=["market"])
async def market_data(city: str):
    data = {
        "Mumbai":     {"avg_rent": 55000, "yoy": 8.2, "demand": "Very High", "forecast": 6.0},
        "Delhi":      {"avg_rent": 38000, "yoy": 5.1, "demand": "High",      "forecast": 5.0},
        "Bangalore":  {"avg_rent": 32000, "yoy": 11.4,"demand": "Very High", "forecast": 9.0},
        "Hyderabad":  {"avg_rent": 24000, "yoy": 9.2, "demand": "High",      "forecast": 8.0},
        "Chennai":    {"avg_rent": 22000, "yoy": 6.8, "demand": "Moderate",  "forecast": 5.0},
        "Pune":       {"avg_rent": 20000, "yoy": 7.5, "demand": "High",      "forecast": 7.0},
        "Kolkata":    {"avg_rent": 16000, "yoy": 3.2, "demand": "Moderate",  "forecast": 4.0},
        "Ahmedabad":  {"avg_rent": 14000, "yoy": 4.8, "demand": "Moderate",  "forecast": 5.0},
        "Jaipur":     {"avg_rent": 12000, "yoy": 5.5, "demand": "Moderate",  "forecast": 5.0},
        "Lucknow":    {"avg_rent": 10000, "yoy": 4.1, "demand": "Low-Moderate","forecast": 4.0},
    }
    if city not in data:
        raise HTTPException(404, f"City '{city}' not found")
    return {"city": city, **data[city]}

# --- Favorites ---
@app.post("/favorites", tags=["favorites"])
async def save_favorite(prediction_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    pred = await db["predictions"].find_one({"_id": prediction_id, "user_id": user["_id"]})
    if not pred:
        raise HTTPException(404, "Prediction not found")
    await db["favorites"].update_one(
        {"user_id": user["_id"], "prediction_id": prediction_id},
        {"$setOnInsert": {"user_id": user["_id"], "prediction_id": prediction_id,
                          "saved_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"status": "saved"}

@app.get("/favorites", tags=["favorites"])
async def get_favorites(db=Depends(get_db), user=Depends(get_current_user)):
    fav_ids = [f["prediction_id"] async for f in db["favorites"].find({"user_id": user["_id"]})]
    preds = await db["predictions"].find({"_id": {"$in": fav_ids}}).to_list(length=50)
    for p in preds:
        p["_id"] = str(p["_id"])
    return {"favorites": preds}

# ─── Entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rentiq_backend:app", host="0.0.0.0", port=8000, reload=True)
