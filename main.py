import requests
import json
import lightgbm as lgb
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import time
from threading import Thread

app = FastAPI()
model = None
trained_sessions = set()

TRAINED_FILE = "trained_sessions.json"

# Load các phiên đã huấn luyện trước đó nếu có
if os.path.exists(TRAINED_FILE):
    with open(TRAINED_FILE, "r") as f:
        try:
            trained_sessions = set(json.load(f))
        except:
            trained_sessions = set()

# Lưu toàn bộ session đã huấn luyện (KHÔNG GIỚI HẠN)
def save_trained_sessions():
    try:
        with open(TRAINED_FILE, "w") as f:
            json.dump(list(trained_sessions), f)
        print(f"💾 Đã lưu {len(trained_sessions)} phiên vào trained_sessions.json")
    except Exception as e:
        print("❌ Lỗi khi lưu trained_sessions.json:", e)

# Lấy dữ liệu lịch sử từ API
def fetch_data():
    try:
        res = requests.get("https://saolo-binhtool.onrender.com/api/taixiu/history")
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data
    except Exception as e:
        print("⚠️ Lỗi khi fetch dữ liệu:", e)
        return []

# Xây dựng đặc trưng từ dữ liệu
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
    return pd.DataFrame(rows)

# Luồng chạy nền tự huấn luyện khi có phiên mới
def auto_train():
    global model, trained_sessions
    while True:
        data = fetch_data()
        if len(data) < 15:
            time.sleep(5)
            continue

        latest_session = data[0]["session"]
        if latest_session in trained_sessions:
            time.sleep(2)
            continue

        df = build_features(data)
        X = df.drop("label", axis=1)
        y = df["label"]

        model = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1)
        model.fit(X, y)

        trained_sessions.add(latest_session)
        save_trained_sessions()
        print(f"✅ Huấn luyện xong phiên {latest_session}")
        time.sleep(2)

# Khi server khởi động
@app.on_event("startup")
def start_background():
    Thread(target=auto_train, daemon=True).start()

@app.get("/")
def home():
    return {"message": "✅ AI Dự đoán Tài/Xỉu đang hoạt động!"}

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