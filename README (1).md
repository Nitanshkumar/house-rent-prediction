# 🏡 RentIQ — AI-Powered House Rent Prediction Platform

> Full-stack AI SaaS platform for Indian rental market intelligence.
> Built with React · FastAPI · scikit-learn · MongoDB Atlas · Claude API

---

## ✨ Features

| Category | Details |
|----------|---------|
| **ML Models** | Random Forest · XGBoost · Neural Network · Linear Regression |
| **AI Assistant** | Claude-powered chatbot for real estate advice |
| **Market Intelligence** | Live trends, city comparisons, AI-generated analysis |
| **Auth** | JWT authentication, bcrypt password hashing |
| **Database** | MongoDB Atlas — users, predictions, chat history, favorites |
| **UI** | Dark glassmorphism, animated gradients, cyberpunk aesthetic |

---

## 🚀 Quick Start

### 1. Clone & configure environment
```bash
git clone https://github.com/yourname/rentiq.git
cd rentiq
cp .env.example .env
# Fill in your keys in .env
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python train_pipeline.py          # Train ML models first
uvicorn rentiq_backend:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm start
# Open http://localhost:3000
```

---

## 📁 Project Structure

```
rentiq/
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Route pages
│   │   ├── hooks/            # Custom React hooks
│   │   ├── utils/            # API helpers
│   │   └── App.jsx           # Root — RentIQ.jsx
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/
│   ├── rentiq_backend.py     # FastAPI app
│   ├── train_pipeline.py     # ML training
│   ├── best_model.pkl        # Saved model (generated)
│   └── requirements.txt
│
├── .env.example
└── README.md
```

---

## 🔑 Environment Variables

```env
# .env.example

# Backend
SECRET_KEY=your-super-secret-jwt-key-change-in-production
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/?retryWrites=true
ANTHROPIC_API_KEY=sk-ant-...

# Frontend (create .env in /frontend)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🗃️ MongoDB Collections

```json
// users
{ "_id": "uuid", "name": "...", "email": "...", "password": "<bcrypt>", "created_at": "..." }

// predictions
{ "_id": "uuid", "user_id": "...", "input": {...}, "result": {...}, "timestamp": "..." }

// chat_history
{ "_id": "uuid", "user_id": "...", "messages": [...], "timestamp": "..." }

// favorites
{ "_id": "uuid", "user_id": "...", "prediction_id": "...", "saved_at": "..." }
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ❌ | Register new user |
| POST | `/login` | ❌ | Login → JWT token |
| GET | `/me` | ✅ | Current user profile |
| POST | `/predict` | ✅ | Predict rent (saved) |
| POST | `/predict/guest` | ❌ | Predict (unauthenticated, rate-limited) |
| GET | `/history` | ✅ | Prediction history |
| GET | `/analytics` | ✅ | Analytics & metrics |
| GET | `/models` | ❌ | ML model performance |
| POST | `/train` | ✅ | Retrain models |
| POST | `/chat` | ✅ | AI chatbot (Claude) |
| GET | `/market/{city}` | ❌ | City market data |
| POST | `/favorites` | ✅ | Save a prediction |
| GET | `/favorites` | ✅ | Get saved predictions |

---

## 🤖 ML Pipeline

```
Raw Input
    ↓
Feature Engineering (parking, amenities, floor bonuses)
    ↓
ColumnTransformer
  ├── StandardScaler (numeric features)
  └── OneHotEncoder (city, furnishing)
    ↓
Model Ensemble
  ├── Random Forest (best accuracy ~93%)
  ├── XGBoost (fast, ~92%)
  ├── Neural Network (MLP, ~91%)
  └── Linear Regression (baseline, ~82%)
    ↓
Prediction + Confidence Interval + Percentile
    ↓
Claude AI Explanation
```

---

## 🚢 Deployment

### Frontend → Vercel
```bash
cd frontend
vercel --prod
# Set env: REACT_APP_API_URL=https://rentiq-api.onrender.com
```

### Backend → Render
1. Create a new **Web Service** on render.com
2. Build command: `pip install -r requirements.txt && python train_pipeline.py`
3. Start command: `uvicorn rentiq_backend:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Render dashboard

### Database → MongoDB Atlas
1. Create a free M0 cluster at cloud.mongodb.com
2. Whitelist `0.0.0.0/0` for Render's dynamic IPs
3. Copy the connection string to `MONGO_URI`

---

## 📦 requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
scikit-learn==1.4.2
xgboost==2.0.3
pandas==2.2.2
numpy==1.26.4
joblib==1.4.2
pymongo==4.7.2
motor==3.4.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pydantic==2.7.1
anthropic==0.26.0
python-dotenv==1.0.1
slowapi==0.1.9
httpx==0.27.0
```

---

## 🧪 ML Model Performance

| Model | R² Score | MAE | RMSE |
|-------|----------|-----|------|
| Random Forest | **0.934** | ₹2,840 | ₹3,960 |
| XGBoost | 0.921 | ₹3,120 | ₹4,280 |
| Neural Network | 0.908 | ₹3,450 | ₹4,710 |
| Linear Regression | 0.823 | ₹5,200 | ₹7,100 |

---

## 🛡️ Security

- JWT tokens with configurable expiry
- bcrypt password hashing (12 rounds)
- Rate limiting (slowapi) — 30 req/min for predictions
- CORS configured per environment
- All secrets via environment variables
- MongoDB Atlas IP allowlisting

---

*Built with ❤️ as a portfolio-grade AI SaaS project.*
