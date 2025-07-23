import requests
import json
import lightgbm as lgb
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()
model = None

# Lấy lịch sử
def fetch_data():
    try:
        res = requests.get("https://saolo-binhtool.onrender.com/api/taixiu/history")
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data
    except:
        return []

# Chuyển đổi dữ liệu để train
def build_features(data, depth=5):
    rows = []
    for i in range(depth, len(data)):
        row = {}
        for j in range(depth):
            item = data[i - j]
            row[f'd{j+1}_1'] = item['dice'][0]
            row[f'd{j+1}_2'] = item['dice'][1]
            row[f'd{j+1}_3'] = item['dice'][2]
            row[f'total{j+1}'] = item['total']
        label = data[i]["result"]
        row["label"] = 1 if label == "Tài" else 0
        rows.append(row)
    df = pd.DataFrame(rows)
    return df

@app.on_event("startup")
def startup():
    global model
    data = fetch_data()
    if len(data) < 15:
        return
    df = build_features(data)
    X = df.drop("label", axis=1)
    y = df["label"]
    model = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1)
    model.fit(X, y)

@app.get("/")
def home():
    return {"message": "AI Dự đoán Tài/Xỉu (LightGBM 5 phiên) đang chạy..."}

@app.get("/predict")
def predict():
    global model
    data = fetch_data()
    if len(data) < 10 or model is None:
        return JSONResponse(content={"error": "Thiếu dữ liệu hoặc chưa huấn luyện xong"})

    latest_df = build_features(data[-10:], depth=5)
    latest = latest_df.drop("label", axis=1).iloc[-1:]
    prob = model.predict_proba(latest)[0]
    du_doan = "Tài" if prob[1] > prob[0] else "Xỉu"

    current = data[0]
    return {
        "current_session": current["session"],
        "dice": current["dice"],
        "total": current["total"],
        "result": current["result"],
        "next_session": current["session"] + 1,
        "du_doan_AI": du_doan,
        "confidence": f"{round(max(prob)*100, 2)}%",
        "AI": "AI NÂNG CAO MR_SIMON",
        "Telegram": "@ExTaiXiu2010"
    }