import requests
import json
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

app = FastAPI()
model_path = "model_catboost.pkl"
model = None

# ------------------- Lấy dữ liệu -------------------
def fetch_data():
    try:
        res = requests.get("https://saobody-lopq.onrender.com/api/taixiu/history")
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data[:200]  # Dùng 200 phiên gần nhất
    except:
        return []

# ------------------- Tạo đặc trưng -------------------
def build_features(data, depth=10):
    rows = []
    for i in range(depth, len(data)):
        row = {}
        tai_count = 0
        total_sum = 0
        odd_even_count = 0

        for j in range(depth):
            item = data[i - j - 1]
            d1, d2, d3 = item['dice']
            total = item['total']
            is_tai = item['result'] == "Tài"

            row[f'd{j+1}_1'] = d1
            row[f'd{j+1}_2'] = d2
            row[f'd{j+1}_3'] = d3
            row[f'total{j+1}'] = total

            tai_count += int(is_tai)
            total_sum += total
            odd_even_count += sum(x % 2 for x in [d1, d2, d3])

        # Thêm các feature thống kê
        row["tai_count"] = tai_count
        row["avg_total"] = total_sum / depth
        row["odd_count"] = odd_even_count

        label = data[i]["result"]
        row["label"] = 1 if label == "Tài" else 0
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

# ------------------- Huấn luyện mô hình -------------------
def train_model():
    global model
    data = fetch_data()
    if len(data) < 50:
        print("Không đủ dữ liệu")
        return

    df = build_features(data, depth=10)
    X = df.drop("label", axis=1)
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CatBoostClassifier(
        iterations=300,
        learning_rate=0.05,
        depth=6,
        random_seed=42,
        verbose=False
    )
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"🎯 Độ chính xác (test set): {acc * 100:.2f}%")
    joblib.dump(model, model_path)
    print("✅ Đã lưu model CatBoost")

# ------------------- Khởi động API -------------------
@app.on_event("startup")
def startup_event():
    global model
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print("✅ Tải model từ file")
    else:
        train_model()

# ------------------- Trang chủ -------------------
@app.get("/")
def home():
    return {"message": "🎲 API Dự đoán Tài/Xỉu bằng CatBoost AI đã sẵn sàng."}

# ------------------- Dự đoán -------------------
@app.get("/predict")
def predict():
    global model
    data = fetch_data()
    if len(data) < 20 or model is None:
        return JSONResponse(content={"error": "Thiếu dữ liệu hoặc mô hình chưa sẵn sàng."})

    df = build_features(data, depth=10)
    latest = df.drop("label", axis=1).iloc[-1:]
    prob = model.predict_proba(latest)[0]
    pred_class = model.predict(latest)[0]
    pred_prob = prob[pred_class]
    confidence = max(0.5, min(0.99, pred_prob))

    du_doan = "Tài" if pred_class == 1 else "Xỉu"
    current = data[0]

    return {
        "current_session": current["session"],
        "dice": current["dice"],
        "total": current["total"],
        "result": current["result"],
        "next_session": current["session"] + 1,
        "du_doan_Api": du_doan,
        "confidence": f"{round(confidence * 100, 2)}%",
        "version": "SIMON SYSTEM V1",
        "data_used": f"{len(data)} phiên",
        "telegram": "@ExTaiXiu2010"
    }

# ------------------- Tự cập nhật mô hình -------------------
@app.get("/update_model")
def update_model():
    train_model()
    return {"message": "✅ Đã cập nhật mô hình CatBoost từ dữ liệu mới"}