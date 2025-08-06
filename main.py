from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random
from collections import Counter
import json
import requests

app = FastAPI()

# ------------------- Bật CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain, bạn có thể giới hạn nếu cần
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Công thức cầu -------------------
def xu_huong_diem(history):
    total1 = history[1]["total"]
    total2 = history[0]["total"]
    if total2 > total1:
        return "lên"
    elif total2 < total1:
        return "xuống"
    else:
        return "đều"

def dem_trung(xucxac):
    return max(xucxac.count(i) for i in xucxac)

def dem_tan_suat(xx1, xx2, xx3):
    return Counter(xx1 + xx2 + xx3)

def du_doan_theo_cong_thuc(history):
    try:
        xx1 = history[2]["dice"]
        xx2 = history[1]["dice"]
        xx3 = history[0]["dice"]
        total2 = history[1]["total"]
        total3 = history[0]["total"]
        result3 = history[0]["result"]
        trend = xu_huong_diem(history)

        freq = dem_tan_suat(xx1, xx2, xx3)

        if dem_trung(xx1) == 3:
            return "Tài" if trend == "lên" else "Xỉu"
        elif dem_trung(xx1) == 2:
            return "Tài" if trend == "lên" else "Xỉu"
        elif dem_trung(xx2) == 3:
            return "Tài" if trend == "lên" else "Xỉu"

        if (abs(xx3[0] - xx3[1]) == 1 and abs(xx3[2] - xx3[1]) == 1) or \
           (abs(xx3[1] - xx3[2]) == 1 and abs(xx3[0] - xx3[1]) == 1):
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        sorted_xx = sorted(xx3)
        if sorted_xx[1] == sorted_xx[0] + 1 and sorted_xx[2] == sorted_xx[1] + 1:
            return result3

        if sorted_xx[1] - sorted_xx[0] == 2 and sorted_xx[2] - sorted_xx[1] == 2:
            return result3

        if dem_trung(xx3) == 3:
            if xx3[0] in [3, 4, 6]:
                return result3
            else:
                return "Tài" if result3 == "Xỉu" else "Xỉu"

        if dem_trung(xx3) == 2:
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        return result3
    except:
        return None

# ------------------- Fetch dữ liệu -------------------
def fetch_data():
    try:
        res = requests.get("https://binhtool90-sunwin-predict.onrender.com/api/taixiu/history")
        lines = res.text.strip().splitlines()
        data = [json.loads(line) for line in lines if line.strip()]
        return data
    except Exception as e:
        print(f"Lỗi fetch: {e}")
        return []

# ------------------- API Dự đoán -------------------
@app.get("/predict")
def predict():
    data = fetch_data()
    if len(data) < 3:
        return JSONResponse(content={"error": "Thiếu dữ liệu."})

    du_doan = du_doan_theo_cong_thuc(data[:3])
    if du_doan is None:
        du_doan = random.choice(["Tài", "Xỉu"])
        confidence = 0.5
    else:
        confidence = 0.95

    current = data[0]
    dice = current["dice"]

    return {
        "id": "ExTaiXiu2010",
        "phien": current["session"],
        "xuc_xac_1": dice[0],
        "xuc_xac_2": dice[1],
        "xuc_xac_3": dice[2],
        "tong": current["total"],
        "ket_qua": current["result"],
        "du_doan": du_doan,
        "ty_le_thanh_cong": f"{round(confidence * 100, 2)}%"
    }